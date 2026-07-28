"""
语义匹配引擎
- 语义分 (cosine similarity) 为主
- 领域圈过滤
- 关键词补分 (abstract缺失时)
"""
import json
import re
from database.database import SessionLocal
from database.models import UserInterest, PaperEmbedding, TopicArticleMatch
from services.matching.encoder import cosine_similarity, get_or_compute_embedding, encode_user_interest
from services.domain.domain_keywords import domain_matches
MIN_SEMANTIC_SCORE = 0.25
KEYWORD_BONUS = 0.03
MUST_INCLUDE_BONUS = 0.05


def split_keywords(value):
    if not value:
        return []
    return [k.strip().lower() for k in re.split(r"[;,、；，]", str(value)) if k.strip()]


def count_keyword_hits(text, keywords):
    if not text:
        return []
    hits = []
    for kw in keywords:
        if not kw:
            continue
        pattern = re.compile(r'(?<![a-zA-Z0-9])' + re.escape(kw) + r'(?![a-zA-Z0-9])', re.IGNORECASE)
        if pattern.search(text):
            hits.append(kw)
    return hits


def match_interest_against_papers(interest: UserInterest, papers: list, db) -> list:
    """Match a user interest against a list of paper dicts, return matches"""
    interest_vec = _get_interest_vector(interest)
    if interest_vec is None:
        return []

    wanted_domains = [d.strip() for d in (interest.domain or "").split(",") if d.strip()]
    interest_keywords = split_keywords(interest.keywords)
    matches = []

    for paper in papers:
        doi = paper.get("doi") or getattr(paper, "doi", "")
        if not doi:
            continue

        # Domain filter
        paper_domain = getattr(paper, "domain", None) or paper.get("domain", "")
        if not domain_matches(paper_domain, wanted_domains):
            continue

        # Get or compute paper embedding
        title = getattr(paper, "title", "") or paper.get("title", "")
        abstract = getattr(paper, "abstract", "") or paper.get("abstract", "")
        summary = getattr(paper, "summary", "") or paper.get("summary", "")
        paper_text = f"{title}. {abstract or summary or ''}"

        paper_vec = get_or_compute_embedding(doi, title, abstract, summary, paper_domain)
        if paper_vec is None:
            continue

        # Semantic score
        semantic = cosine_similarity(interest_vec, paper_vec)
        if semantic < MIN_SEMANTIC_SCORE:
            continue

        # Keyword bonus (when abstract is sparse)
        total = semantic
        if interest_keywords:
            kw_hits = count_keyword_hits(paper_text, interest_keywords)
            total += len(kw_hits) * KEYWORD_BONUS
            if len(kw_hits) > 0:
                total += MUST_INCLUDE_BONUS

        matches.append({
            "doi": doi,
            "title": title,
            "semantic_score": round(semantic, 4),
            "score": round(min(total, 1.0), 4),
            "matched_keywords": interest_keywords if interest_keywords else [],
        })

    matches.sort(key=lambda x: x["score"], reverse=True)
    return matches[:10]


def _get_interest_vector(interest: UserInterest) -> list:
    if interest.vector:
        try:
            return json.loads(interest.vector)
        except Exception:
            pass
    # Compute and cache
    vec = encode_user_interest(interest.description, interest.keywords, interest.llm_expanded)
    if vec is None:
        return None
    interest.vector = json.dumps(vec)
    db2 = SessionLocal()
    try:
        db2.merge(interest)
        db2.commit()
    except Exception:
        db2.rollback()
    finally:
        db2.close()
    return vec
