"""
Job Worker - 基于数据库的任务队列

支持：
- claim/lock 机制防重复处理
- 指数退避重试（60s → 300s → 1800s）
- 多 Job 类型分发
- 进度追踪
"""
import json
import threading
import time
from datetime import datetime, timedelta
from typing import Optional, Callable

from database.database import SessionLocal
from database.models import User, Job, JournalFetchState, Journal, UserJournalFollow, TopicSubscription, UserInterest, TopicArticleMatch, WeeklyReport, Paper, TopicFeedback, EmailDelivery
from services.sources.rss.collector import collect_all_journals
from services.email.smtp_sender import send_daily_email, send_email_to
from services.config.subscription import load_subscription
from services.core.semantic_match import match_topic, expand_query


JOB_LOCK_TTL_SECONDS = 900
JOB_POLL_INTERVAL = 10
RETRY_DELAYS = [60, 300, 1800]


# ==========================================================
# Job 操作
# ==========================================================

def enqueue_job(
    job_type: str,
    user_id: Optional[int] = None,
    payload: Optional[dict] = None,
    run_after: Optional[datetime] = None,
    max_attempts: int = 3,
):
    db = SessionLocal()
    try:
        job = Job(
            type=job_type,
            status="PENDING",
            user_id=user_id,
            payload=json.dumps(payload or {}),
            run_after=run_after or datetime.now(),
            max_attempts=max_attempts,
        )
        db.add(job)
        db.commit()
        return job.id
    finally:
        db.close()


def claim_next_job(lock_owner: str = "worker") -> Optional[Job]:
    """Claim the next available job with lock"""
    db = SessionLocal()
    try:
        now = datetime.now()
        lock_expired_before = now - timedelta(seconds=JOB_LOCK_TTL_SECONDS)

        candidate = db.query(Job).filter(
            Job.status.in_(["PENDING", "RETRYING"]),
            Job.run_after <= now,
        ).order_by(Job.run_after, Job.created_at).first()

        if not candidate:
            candidate = db.query(Job).filter(
                Job.status == "RUNNING",
                Job.locked_at <= lock_expired_before,
            ).order_by(Job.run_after, Job.created_at).first()

        if not candidate:
            return None

        candidate.status = "RUNNING"
        candidate.attempts = (candidate.attempts or 0) + 1
        candidate.locked_at = now
        candidate.lock_owner = lock_owner
        candidate.started_at = now
        candidate.last_error = ""
        db.commit()
        db.refresh(candidate)
        return candidate
    finally:
        db.close()


def complete_job(job_id: int, progress: Optional[dict] = None):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        job.status = "SUCCESS"
        job.progress = json.dumps(progress or {})
        job.completed_at = datetime.now()
        job.locked_at = None
        job.lock_owner = ""
        job.last_error = ""
        db.commit()
    finally:
        db.close()


def fail_job(job_id: int, error: str, progress: Optional[dict] = None):
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return

        attempts = job.attempts or 0
        max_attempts = job.max_attempts or 3

        if attempts >= max_attempts:
            job.status = "FAILED"
            job.completed_at = datetime.now()
            job.locked_at = None
            job.lock_owner = ""
            job.last_error = error
        else:
            delay = RETRY_DELAYS[min(attempts - 1, len(RETRY_DELAYS) - 1)]
            job.status = "RETRYING"
            job.run_after = datetime.now() + timedelta(seconds=delay)
            job.locked_at = None
            job.lock_owner = ""
            job.last_error = error

        job.progress = json.dumps(progress or {})
        db.commit()
    finally:
        db.close()


# ==========================================================
# Job 处理器
# ==========================================================

JOB_HANDLERS = {}


def register_handler(job_type: str):
    def decorator(func):
        JOB_HANDLERS[job_type] = func
        return func
    return decorator


@register_handler("FETCH_JOURNAL")
def handle_fetch_journal(job: Job):
    """采集所有活跃期刊的 RSS 论文 + 自动话题匹配"""
    import json as _json
    payload = json.loads(job.payload or "{}")
    limit = payload.get("limit", 50)
    timeout = payload.get("timeout", 300)

    papers = collect_all_journals(limit=limit, timeout=timeout)

    # Enrich papers with abstracts via CrossRef DOI lookup
    if papers:
        dois = [p.doi for p in papers if p.doi and not p.abstract]
        if dois:
            print(f"[FETCH] Resolving {len(dois)} DOIs for abstracts...")
            from services.sources.crossref import batch_enrich_all_sources
            abstracts = batch_enrich_all_sources(dois)
            for p in papers:
                if p.doi and p.doi in abstracts:
                    p.abstract = abstracts[p.doi]
            print(f"[FETCH] Enriched {len(abstracts)} papers with abstracts")

    # Persist collected papers to papers table for search
    if papers:
        db3 = SessionLocal()
        try:
            for rss_paper in papers:
                if not rss_paper.doi:
                    continue
                existing = db3.query(Paper).filter(Paper.doi == rss_paper.doi).first()
                if not existing:
                    yr = 0
                    pub_date = rss_paper.published or ""
                    if pub_date:
                        try:
                            yr = int(pub_date[:4])
                        except:
                            yr = 0
                    orm_paper = Paper(
                        title=rss_paper.title,
                        abstract=rss_paper.abstract or rss_paper.summary or "",
                        authors=", ".join(rss_paper.authors) if rss_paper.authors else "",
                        year=yr,
                        publication_date=pub_date,
                        doi=rss_paper.doi,
                        url=rss_paper.url,
                        journal=rss_paper.journal,
                        publisher=rss_paper.publisher,
                        keywords=";".join(rss_paper.keywords) if rss_paper.keywords else "",
                        subjects=";".join(rss_paper.subjects) if rss_paper.subjects else "",
                        source=rss_paper.source or "RSS",
                        doi_url=f"https://doi.org/{rss_paper.doi}",
                    )
                    db3.add(orm_paper)
            db3.commit()
        finally:
            db3.close()

    # Compute embeddings for newly persisted papers (for future matching)
    if papers:
        from services.domain.domain_keywords import get_paper_domain
        from services.matching.encoder import get_or_compute_embedding
        for p in papers:
            if p.doi and p.title:
                txt = f"{p.title} {p.abstract or p.summary or ''}"
                dom = get_paper_domain(p.journal or "", txt)
                get_or_compute_embedding(p.doi, p.title, p.abstract or p.summary or "", "", dom)

    return {
        "stage": "DONE",
        "papers_collected": len(papers),
        "topic_matches_created": 0,
        "email_deliveries_enqueued": 0,
    }


@register_handler("SEND_EMAIL")
def handle_send_email(job: Job):
    """发送邮件（每日推送或话题通知）"""
    payload = json.loads(job.payload or "{}")
    kind = payload.get("kind", "daily")

    if kind == "daily":
        result = send_daily_email()
        return {"stage": "DONE", "email_result": result}

    if kind == "topic_notification":
        to_email = payload.get("to_email", "")
        subject = payload.get("subject", "ChemVigil Topic Notification")
        html = payload.get("html", "")
        if to_email:
            result = send_email_to(to_email=to_email, subject=subject, html_content=html)
            _record_delivery(
                user_id=payload.get("user_id"),
                kind="test",
                status="SENT" if result.get("status") == "success" else "FAILED",
                to_email=to_email,
                subject=subject,
                error_message=str(result.get("message", "")) if result.get("status") != "success" else None,
            )
            return {"stage": "DONE", "email_result": result}
        return {"stage": "DONE", "email_result": {"status": "skipped", "message": "No recipient"}}

    return {"stage": "DONE", "email_result": {"status": "skipped", "message": f"Unknown kind: {kind}"}}


@register_handler("NEW_ARTICLES")
def handle_new_articles(job: Job):
    """匹配全库论文→用户兴趣，发送推送邮件"""
    import traceback
    payload = json.loads(job.payload or "{}")
    user_id = payload.get("user_id")
    if not user_id:
        return {"stage": "DONE", "email_result": {"status": "skipped", "message": "No user_id"}}

    match_limit = payload.get("match_limit", 200)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user or not user.target_email:
            return {"stage": "DONE", "email_result": {"status": "skipped", "message": "User or email not found"}}

        # Get user's enabled interests
        interests = db.query(UserInterest).filter(
            UserInterest.user_id == user_id,
            UserInterest.enabled == True,
        ).all()
        if not interests:
            return {"stage": "DONE", "email_result": {"status": "skipped", "message": "No enabled interests"}}

        from collections import defaultdict
        from services.domain.domain_keywords import get_paper_domain
        from services.matching.matcher import match_interest_against_papers
        from services.matching.encoder import get_or_compute_embedding

        # Collect all existing match DOIs for this user (to skip)
        matched_dois = set()
        for interest in interests:
            for m in db.query(TopicArticleMatch).filter(
                TopicArticleMatch.interest_id == interest.id
            ).all():
                matched_dois.add(m.article_doi)

        # Query papers from DB that have abstracts, excluding already-matched DOIs
        db_papers = db.query(Paper).filter(
            Paper.abstract.isnot(None),
            Paper.abstract != "",
            ~Paper.doi.in_(matched_dois) if matched_dois else True,
        ).limit(match_limit).all()

        if not db_papers:
            return {"stage": "DONE", "email_result": {"status": "skipped", "message": "No new papers to match"}}

        # Convert to dicts and compute embeddings
        paper_dicts = []
        for p in db_papers:
            if not p.doi or not p.title:
                continue
            txt = f"{p.title} {p.abstract or ''}"
            dom = get_paper_domain(p.journal or "", txt)
            paper_dicts.append({
                "doi": p.doi,
                "title": p.title,
                "abstract": p.abstract or "",
                "summary": "",
                "domain": dom,
                "journal": p.journal or "",
            })
            get_or_compute_embedding(p.doi, p.title, p.abstract or "", "", dom)

        # Match all papers against all user interests
        all_new_matches = []
        for interest in interests:
            matches = match_interest_against_papers(interest, paper_dicts, db)
            for m in matches:
                # Re-check dedup (in case concurrent writes)
                existing = db.query(TopicArticleMatch).filter(
                    TopicArticleMatch.interest_id == interest.id,
                    TopicArticleMatch.article_doi == m["doi"],
                ).first()
                if existing:
                    continue
                match = TopicArticleMatch(
                    user_id=user_id,
                    interest_id=interest.id,
                    article_doi=m["doi"],
                    article_title=m["title"],
                    matched_keywords=json.dumps(m["matched_keywords"]),
                    score=m["score"],
                    semantic_score=m["semantic_score"],
                )
                db.add(match)
                all_new_matches.append(match)

        db.commit()

        if not all_new_matches:
            return {"stage": "DONE", "email_result": {"status": "skipped", "message": "No new matches found"}}

        # Build email with all matches
        paper_cache = {}
        dois = [m.article_doi for m in all_new_matches if m.article_doi]
        for p in db.query(Paper).filter(Paper.doi.in_(dois)).all():
            paper_cache[p.doi] = p

        by_interest = defaultdict(list)
        interest_names = {}
        for m in all_new_matches:
            by_interest[m.interest_id].append(m)
            if m.interest_id not in interest_names:
                t = db.query(UserInterest).filter(UserInterest.id == m.interest_id).first()
                interest_names[m.interest_id] = t.name if t else f"Interest-{m.interest_id}"

        articles_html = ""
        for iid, mlist in sorted(by_interest.items(), key=lambda x: len(x[1]), reverse=True):
            articles_html += f'<h3 style="color:#2456c3;font-size:18px;margin:32px 0 16px;">Research Topic: {interest_names[iid]}</h3>'
            for m in mlist[:20]:
                doi_url = f"https://doi.org/{m.article_doi}" if m.article_doi else ""
                paper = paper_cache.get(m.article_doi)
                authors = paper.authors if paper and paper.authors else ""
                journal = paper.journal if paper and paper.journal else ""
                abstract = paper.abstract if paper and paper.abstract else ""
                kw_str = ""
                try:
                    kw_list = json.loads(m.matched_keywords or "[]")
                    kw_str = ", ".join(kw_list[:5])
                except Exception:
                    kw_str = m.matched_keywords or ""

                articles_html += f"""<div class="paper-card">
<h2>{m.article_title}</h2>
<p><b>Match Score</b><br>{m.score:.2f}</p>"""
                if authors:
                    articles_html += f'<p><b>Authors</b><br>{authors}</p>'
                if journal:
                    articles_html += f'<p><b>Journal</b><br>{journal}</p>'
                if kw_str:
                    articles_html += f'<p><b>Keywords</b><br>{kw_str}</p>'
                if abstract:
                    articles_html += f'<p><b>Abstract</b><br>{abstract[:500]}</p>'
                articles_html += f"""<p>
<a class="button" href="{doi_url}" target="_blank">View on Publisher</a>
</p>
</div>"""

        html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
body{{margin:0;padding:40px;background:#f5f7fb;font-family:Arial,sans-serif;}}
.container{{width:900px;margin:auto;}}
.header{{background:white;border-radius:18px;padding:35px;margin-bottom:35px;box-shadow:0 5px 20px rgba(0,0,0,.08);}}
.logo{{font-size:46px;font-weight:bold;color:#2456c3;}}
.subtitle{{color:#666;margin-top:8px;}}
.date{{color:#999;margin-top:15px;}}
h2{{margin:0 0 8px;}}
.paper-card{{background:white;border-radius:16px;padding:28px;margin-bottom:28px;box-shadow:0 5px 18px rgba(0,0,0,.08);}}
.paper-card h2{{color:#2456c3;line-height:1.4;}}
.paper-card p{{line-height:1.8;}}
.button{{display:inline-block;margin-top:10px;margin-right:10px;padding:10px 18px;background:#2456c3;color:white;border-radius:8px;text-decoration:none;}}
.footer{{margin-top:50px;text-align:center;color:#999;}}
</style>
</head>
<body>
<div class="container">
<div class="header">
<div class="logo">ChemVigil</div>
<div class="subtitle">Intelligent Literature Discovery Platform</div>
<h2>Literature Matches</h2>
<p>Hi {user.name}, we found <strong>{len(all_new_matches)}</strong> new papers matching your research interests.</p>
<div class="date">Generated on {datetime.now().strftime('%Y-%m-%d')}</div>
</div>
{articles_html}
<div class="footer">Generated automatically by ChemVigil</div>
</div>
</body>
</html>"""

        subject = f"ChemVigil - {len(all_new_matches)} new article matches"
        result = send_email_to(to_email=user.target_email, subject=subject, html_content=html)

        status = "SENT" if result.get("status") == "success" else "FAILED"
        _record_delivery(
            user_id=user_id, kind="new_articles", status=status,
            to_email=user.target_email, subject=subject,
            article_count=len(all_new_matches),
            error_message=str(result.get("message", "")) if status == "FAILED" else None,
            job_id=job.id,
        )

        return {"stage": "DONE", "email_result": result, "articles": len(all_new_matches)}

    except Exception as e:
        _record_delivery(user_id=user_id, kind="new_articles", status="FAILED",
                         to_email="", subject="", error_message=str(e), job_id=job.id)
        raise
    finally:
        db.close()


@register_handler("ENRICH_ABSTRACTS")
def handle_enrich_abstracts(job: Job):
    """批量补齐全库论文摘要（CrossRef + OpenAlex 双源）"""
    import traceback
    payload = json.loads(job.payload or "{}")
    max_papers = payload.get("max_papers", 500)
    batch_size = payload.get("batch_size", 50)

    db = SessionLocal()
    try:
        # Find papers with DOIs but no abstract
        papers = db.query(Paper).filter(
            Paper.doi.isnot(None),
            Paper.doi != "",
            ((Paper.abstract.is_(None)) | (Paper.abstract == "")),
        ).limit(max_papers).all()

        if not papers:
            return {"stage": "DONE", "enriched": 0, "message": "No papers need enrichment"}

        dois = [p.doi for p in papers if p.doi]
        print(f"[ENRICH] Found {len(dois)} papers without abstracts, enriching...")

        from services.sources.crossref import batch_enrich_all_sources
        total_enriched = 0

        # Process in batches to avoid memory issues
        for i in range(0, len(dois), batch_size):
            batch = dois[i:i + batch_size]
            abstracts = batch_enrich_all_sources(batch, max_workers=3)
            if abstracts:
                for p in papers[i:i + batch_size]:
                    if p.doi in abstracts:
                        p.abstract = abstracts[p.doi]
                db.commit()
                total_enriched += len(abstracts)
                print(f"[ENRICH] Batch {i//batch_size + 1}: +{len(abstracts)} abstracts")

        # Recompute embeddings for newly enriched papers
        if total_enriched:
            from services.domain.domain_keywords import get_paper_domain
            from services.matching.encoder import get_or_compute_embedding
            enriched_count = 0
            for p in papers:
                if p.doi and p.abstract and len(p.abstract) > 50:
                    txt = f"{p.title or ''} {p.abstract}"
                    dom = get_paper_domain(p.journal or "", txt)
                    get_or_compute_embedding(p.doi, p.title or "", p.abstract, "", dom)
                    enriched_count += 1
            print(f"[ENRICH] Computed embeddings for {enriched_count} papers")

        return {"stage": "DONE", "enriched": total_enriched}

    except Exception as e:
        print(f"[ENRICH] Error: {traceback.format_exc()}")


@register_handler("RETRY_EMAILS")
def handle_retry_emails(job: Job):
    """Retry failed email deliveries"""
    db = SessionLocal()
    try:
        failed = db.query(EmailDelivery).filter(
            EmailDelivery.status == "FAILED",
        ).all()
        retried = 0
        for d in failed:
            if d.to_email:
                from services.email.email_provider import send_email
                result = send_email(
                    to_email=d.to_email,
                    subject=d.subject or "ChemVigil Notification",
                    html_content="",
                )
                if result["status"] == "success":
                    d.status = "SENT"
                    d.sent_at = datetime.now()
                    d.error_message = None
                    retried += 1
        db.commit()
        return {"stage": "DONE", "retried": retried, "total_failed": len(failed)}
    finally:
        db.close()


@register_handler("RESOLVE_DOIS")
def handle_resolve_dois(job: Job):
    """通过标题搜索 CrossRef，为无 DOI 论文补全 DOI，然后去重"""
    import traceback, time
    payload = json.loads(job.payload or "{}")
    max_papers = payload.get("max_papers", 1000)
    batch_size = payload.get("batch_size", 50)

    db = SessionLocal()
    try:
        papers = db.query(Paper).filter(
            (Paper.doi.is_(None)) | (Paper.doi == ""),
            Paper.title.isnot(None),
            Paper.title != "",
        ).limit(max_papers).all()

        if not papers:
            return {"stage": "DONE", "resolved": 0, "message": "No papers without DOIs"}

        print(f"[RESOLVE] Found {len(papers)} papers without DOIs")
        import requests
        import urllib.parse
        resolved = 0
        for i in range(0, len(papers), batch_size):
            for paper in papers[i:i + batch_size]:
                if not paper.title or len(paper.title.strip()) < 10:
                    continue
                try:
                    q = urllib.parse.quote(paper.title[:100].strip())
                    resp = requests.get(
                        f"https://api.crossref.org/works?query.title={q}&rows=3",
                        headers={"User-Agent": "ChemVigil/1.0 (mailto:nancy@boehringer-ingelheim.com)"},
                        timeout=10,
                    )
                    if resp.status_code == 200:
                        items = resp.json().get("message", {}).get("items", [])
                        for item in items:
                            doi = item.get("DOI", "")
                            t = ((item.get("title") or [""])[0] or "").strip().rstrip(".")
                            pt = paper.title.strip().rstrip(".")
                            if doi and t and pt and t[:40].lower().startswith(pt[:40].lower()[:len(t[:40])]):
                                paper.doi = doi
                                paper.doi_url = f"https://doi.org/{doi}"
                                resolved += 1
                                break
                except Exception as e:
                    msg = str(e)
                    if "timeout" in msg.lower() or "timed out" in msg.lower():
                        print(f"  Timeout for '{paper.title[:40]}', skipping...")
                    else:
                        print(f"  CrossRef error for '{paper.title[:40]}': {msg}")
                time.sleep(0.3)
            db.commit()
            print(f"[RESOLVE] Batch {i//batch_size + 1}: {resolved} resolved so far")

        # Dedup: keep the one with abstract/DOI, remove duplicates
        dup_count = 0
        for paper in papers:
            if paper.doi:
                dupes = db.query(Paper).filter(
                    Paper.doi == paper.doi,
                    Paper.id != paper.id,
                ).all()
                for d in dupes:
                    # Keep the one with richer data
                    if d.abstract and len(d.abstract) > 50 and (not paper.abstract or len(paper.abstract) < 50):
                        continue
                    db.delete(d)
                    dup_count += 1
        if dup_count:
            db.commit()

        return {"stage": "DONE", "resolved": resolved, "deduped": dup_count}

    except Exception as e:
        print(f"[RESOLVE] Error: {traceback.format_exc()}")
        raise
    finally:
        db.close()


def _record_delivery(user_id=None, kind="", status="PENDING", to_email="",
                     subject="", article_count=0, error_message=None, job_id=None):
    """记录邮件投递结果到 EmailDelivery 表"""
    try:
        db = SessionLocal()
        try:
            delivery = EmailDelivery(
                user_id=user_id, kind=kind, status=status,
                to_email=to_email, subject=subject,
                article_count=article_count,
                error_message=error_message,
                job_id=job_id,
                sent_at=datetime.now() if status in ("SENT", "FAILED") else None,
            )
            db.add(delivery)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        print(f"[EmailDelivery] Failed to record: {e}")


@register_handler("WEEKLY_SUMMARY")
def handle_weekly_summary(job: Job):
    """生成周报 - 查询最近7天的话题匹配结果，生成Markdown报告，并发送邮件"""
    import uuid as _uuid
    from collections import defaultdict

    payload = json.loads(job.payload or "{}")
    target_user_id = payload.get("user_id")
    send_email = payload.get("send_email", False)
    db = SessionLocal()
    try:
        now = datetime.now()
        week_ago = now - timedelta(days=7)

        query = db.query(TopicArticleMatch).filter(
            TopicArticleMatch.created_at >= week_ago,
        )
        if target_user_id:
            query = query.filter(TopicArticleMatch.user_id == target_user_id)
        matches = query.order_by(TopicArticleMatch.created_at.desc()).all()

        if not matches:
            return {"stage": "DONE", "message": "No matches found", "total_matches": 0}

        user_topics = defaultdict(lambda: defaultdict(list))
        user_ids = set()
        for m in matches:
            user_topics[m.user_id][m.topic_id].append(m)
            user_ids.add(m.user_id)

        report_count = 0
        email_count = 0
        for uid in user_ids:
            topics_dict = user_topics[uid]
            topic_names = {}
            total_for_user = 0
            for tid, mlist in topics_dict.items():
                topic_obj = db.query(TopicSubscription).filter(TopicSubscription.id == tid).first()
                topic_names[tid] = topic_obj.name if topic_obj else f"Topic-{tid}"
                total_for_user += len(mlist)

            lines = [
                f"# Weekly Literature Report",
                f"",
                f"**Period**: {week_ago.strftime('%Y-%m-%d')} ~ {now.strftime('%Y-%m-%d')}",
                f"**Generated**: {now.strftime('%Y-%m-%d %H:%M')}",
                f"",
                f"---",
                f"",
            ]
            for tid, mlist in sorted(topics_dict.items(), key=lambda x: len(x[1]), reverse=True):
                lines.append(f"## {topic_names[tid]}")
                lines.append(f"")
                lines.append(f"**Matched articles**: {len(mlist)}")
                lines.append(f"")
                for m in sorted(mlist, key=lambda x: x.score, reverse=True):
                    doi_url = f"https://doi.org/{m.article_doi}" if m.article_doi else ""
                    kw_str = ""
                    try:
                        kw_list = json.loads(m.matched_keywords or "[]")
                        kw_str = "`" + ", ".join(kw_list[:5]) + "`"
                    except Exception:
                        kw_str = m.matched_keywords or ""
                    lines.append(f"- **{m.article_title}**")
                    if kw_str:
                        lines.append(f"  - Keywords: {kw_str}")
                    if doi_url:
                        lines.append(f"  - DOI: {doi_url}")
                    lines.append(f"")

            run_id = str(_uuid.uuid4())[:8]
            report = WeeklyReport(
                user_id=uid,
                run_id=run_id,
                title=f"Weekly Report {now.strftime('%Y-%m-%d')}",
                content_md="\n".join(lines),
                total_matches=total_for_user,
                topic_count=len(topics_dict),
                period_start=week_ago,
                period_end=now,
            )
            db.add(report)
            report_count += 1

            # Send email if user has email enabled
            if send_email:
                user = db.query(User).filter(User.id == uid).first()
                if user and user.email_enabled and user.target_email:
                    html = _build_report_html(report, user.name or f"User-{uid}")
                    try:
                        from services.email.smtp_sender import send_email_to
                        result = send_email_to(
                            to_email=user.target_email,
                            subject=f"ChemVigil Weekly Report - {now.strftime('%Y-%m-%d')}",
                            html_content=html,
                        )
                        if result.get("status") == "success":
                            email_count += 1
                            _record_delivery(
                                user_id=uid, kind="weekly_summary", status="SENT",
                                to_email=user.target_email,
                                subject=f"ChemVigil Weekly Report - {now.strftime('%Y-%m-%d')}",
                                article_count=total_for_user,
                                job_id=job.id,
                            )
                        else:
                            _record_delivery(
                                user_id=uid, kind="weekly_summary", status="FAILED",
                                to_email=user.target_email,
                                subject=f"ChemVigil Weekly Report - {now.strftime('%Y-%m-%d')}",
                                error_message=str(result.get("message", "")),
                                job_id=job.id,
                            )
                    except Exception as e:
                        _record_delivery(
                            user_id=uid, kind="weekly_summary", status="FAILED",
                            to_email=user.target_email,
                            subject=f"ChemVigil Weekly Report - {now.strftime('%Y-%m-%d')}",
                            error_message=str(e),
                            job_id=job.id,
                        )
                        print(f"[WeeklySummary] Email send error for user {uid}: {e}")

        db.commit()
        return {
            "stage": "DONE",
            "reports_generated": report_count,
            "emails_sent": email_count,
            "total_matches": len(matches),
        }

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _build_report_html(report: WeeklyReport, user_name: str) -> str:
    """Convert Markdown weekly report to HTML for email."""
    import re
    md = report.content_md or ""
    html = md
    html = html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    html = re.sub(r"^### (.+)$", r"<h3>\1</h3>", html, flags=re.M)
    html = re.sub(r"^## (.+)$", r"<h2>\1</h2>", html, flags=re.M)
    html = re.sub(r"^# (.+)$", r"<h1>\1</h1>", html, flags=re.M)
    html = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", html)
    html = re.sub(r"`(.+?)`", r"<code>\1</code>", html)
    html = re.sub(r"^- (.+)$", r"<li>\1</li>", html, flags=re.M)
    html = re.sub(r"<li>.*?(?:</li>\n?)+", lambda m: "<ul>" + m.group(0) + "</ul>", html)
    html = re.sub(r"\n\n", r"<br>", html)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8">
<style>
body{{font-family:Arial,sans-serif;padding:20px;background:#f5f7fb;}}
.container{{max-width:700px;margin:auto;background:white;border-radius:16px;padding:30px;}}
h1{{color:#2456c3;}}
h2{{color:#2456c3;border-bottom:2px solid #eee;padding-bottom:8px;}}
ul{{padding-left:20px;}}
li{{margin-bottom:12px;line-height:1.6;}}
code{{background:#f0f0f0;padding:2px 6px;border-radius:4px;font-size:13px;}}
</style></head>
<body>
<div class="container">
<div style="text-align:center;margin-bottom:20px;">
<h1>ChemVigil Weekly Report</h1>
<p style="color:#666;">Hi <strong>{user_name}</strong>, here are your matched articles this week.</p>
</div>
{html}
<div style="text-align:center;margin-top:30px;color:#999;font-size:12px;">
Generated by ChemVigil Intelligent Literature Platform
</div>
</div>
</body>
</html>"""


def process_job(job: Job):
    """Dispatch job to registered handler"""
    handler = JOB_HANDLERS.get(job.type)
    if not handler:
        raise ValueError(f"Unknown job type: {job.type}")

    return handler(job)


# ==========================================================
# Worker 循环
# ==========================================================

class JobWorker:
    def __init__(self, interval: int = JOB_POLL_INTERVAL):
        self.interval = interval
        self._running = False
        self._thread = None

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        print(f"[JobWorker] Started (poll interval={self.interval}s)")

    def stop(self):
        self._running = False
        print("[JobWorker] Stopped")

    def _run(self):
        while self._running:
            try:
                job = claim_next_job()
                if job:
                    print(f"[JobWorker] Processing job {job.id} ({job.type})")
                    try:
                        progress = process_job(job)
                        complete_job(job.id, progress)
                        print(f"[JobWorker] Job {job.id} completed")
                    except Exception as e:
                        print(f"[JobWorker] Job {job.id} failed: {e}")
                        fail_job(job.id, str(e))
                else:
                    time.sleep(self.interval)
            except Exception as e:
                print(f"[JobWorker] Error: {e}")
                time.sleep(self.interval)


worker = JobWorker()
