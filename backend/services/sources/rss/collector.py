"""
RSS 采集器 - 从数据库读取期刊列表，统一采集所有活跃期刊的RSS源

支持：
- ACS（需要browser-act）
- RSC / Nature / Wiley / Elsevier / Springer（HTTP直连）
- 数据库驱动的采集列表
"""
import re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from bs4 import BeautifulSoup
import feedparser
import requests

from database.database import SessionLocal
from database.models import Journal
from services.models.rss_paper import RSSPaper
from services.discovery.rss_normalizer import clean_html, clean_spaces, extract_doi, remove_doi, remove_metadata


BROWSER_ACT = r"C:\Users\luoyihan\.local\bin\browser-act.exe"
SESSION = "acs-batch"


def normalize_entry(entry, source: str, journal_title: str = "", publisher: str = "") -> RSSPaper:
    title = ""
    lt = entry.get("title", "")
    if hasattr(lt, "strip"):
        title = clean_html(str(lt))
    if not title:
        return None

    link = ""
    link_tag = entry.get("link", "")
    if isinstance(link_tag, dict):
        link = str(link_tag.get("href", ""))
    elif hasattr(link_tag, "strip"):
        link = str(link_tag)
    elif isinstance(link_tag, list):
        for l in link_tag:
            if hasattr(l, "get"):
                href = l.get("href", "")
                if href:
                    link = href
                    break

    published = str(entry.get("pubDate", "") or entry.get("published", "") or entry.get("updated", "") or "")

    raw_summary = str(entry.get("summary", "") or entry.get("description", "") or "")
    summary = clean_html(raw_summary)
    doi = extract_doi(raw_summary)
    if not doi:
        doi = extract_doi(link)
    if not doi and summary:
        doi = extract_doi(summary)
    summary = remove_doi(summary)
    summary = remove_metadata(summary)
    summary = clean_spaces(summary)

    abstract = ""
    abstract_tag = entry.get("abstract", "")
    if abstract_tag:
        abstract = clean_html(str(abstract_tag))

    authors_list = []
    dc = entry.get("dc:creator", "")
    if dc:
        if isinstance(dc, str):
            authors_list = [a.strip() for a in dc.split(";") if a.strip()]
        elif isinstance(dc, list):
            authors_list = [str(a) for a in dc]

    keywords = []
    tags = entry.get("tags", [])
    if tags:
        for tag in tags:
            t = tag.get("term", "")
            if t:
                keywords.append(str(t))

    return RSSPaper(
        title=title,
        summary=summary,
        abstract=abstract,
        url=link,
        published=published,
        source=f"{publisher} RSS",
        doi=doi,
        authors=authors_list,
        journal=journal_title,
        publisher=publisher,
        keywords=keywords,
        subjects=keywords,
    )


_BROWSER_OPENED = False
_BROWSER_ID = "108290830888227166"

def _ensure_browser():
    global _BROWSER_OPENED
    if _BROWSER_OPENED:
        return True
    import subprocess
    try:
        r = subprocess.run([BROWSER_ACT, "--session", SESSION, "browser", "open",
                           _BROWSER_ID, "about:blank"], capture_output=True, timeout=30)
        if r.returncode == 0:
            _BROWSER_OPENED = True
            return True
        err = r.stderr.decode("utf-8", errors="replace")[:200] if r.stderr else f"rc={r.returncode}"
        print(f"  browser-act open failed: {err}")
        return False
    except Exception as e:
        print(f"  browser-act open error: {e}")
        return False


def fetch_cloudflare_rss(url: str, journal: str, publisher: str) -> List[RSSPaper]:
    """通过 browser-act 绕过 Cloudflare 采集 RSS"""
    if not _ensure_browser():
        return []
    import subprocess
    papers = []
    try:
        r = subprocess.run([BROWSER_ACT, "--session", SESSION, "navigate", url],
                           capture_output=True, timeout=15)
        if r.returncode != 0:
            return papers
        time.sleep(2)
        r2 = subprocess.run([BROWSER_ACT, "--session", SESSION, "get", "markdown"],
                            capture_output=True, timeout=10)
        if r2.returncode != 0:
            return papers
        content = r2.stdout.decode("utf-8", errors="replace")
        idx = content.find("The document tree is shown below.")
        if idx > 0:
            xml_text = content[idx + len("The document tree is shown below."):].strip()
        else:
            xml_text = content
        soup = BeautifulSoup(xml_text, "xml")
        items = soup.find_all("item")
        for item in items:
            paper = normalize_entry(
                {"title": item.find("title"), "link": item.find("link"),
                 "pubDate": item.find("pubDate"), "summary": item.find("description") or item.find("summary"),
                 "abstract": item.find("abstract")},
                source=publisher or "cloudflare", journal_title=journal, publisher=publisher
            )
            if paper:
                for tag in item.find_all():
                    if "doi" in (tag.name or "").lower():
                        paper.doi = clean_html(str(tag))
                        break
                if not paper.doi:
                    m = re.search(r"10\.\d{4,9}/\S+", paper.url)
                    if m:
                        paper.doi = m.group(0).rstrip(".")
                papers.append(paper)
    except Exception as e:
        print(f"  browser-act error ({journal}): {e}")
    return papers


def fetch_rss_http(url: str, journal: str, publisher: str) -> List[RSSPaper]:
    """普通 HTTP RSS 抓取"""
    papers = []
    try:
        http_url = url.replace("https://", "http://") if "rsc.org" in url else url
        r = requests.get(http_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        r.raise_for_status()
        feed = feedparser.parse(r.text)
        for entry in feed.entries:
            paper = normalize_entry(entry, source=publisher, journal_title=journal, publisher=publisher)
            if paper:
                papers.append(paper)
    except Exception as e:
        print(f"  HTTP fetch error ({journal}): {e}")
    return papers


_CLOUDFLARE_PUBLISHERS = {"ACS", "Wiley"}

def _fetch_one(journal, limit):
    try:
        if journal.publisher in _CLOUDFLARE_PUBLISHERS:
            # Cloudflare 期刊内容已从 home_papers.xlsx 导入，跳过
            return []
        return fetch_rss_http(journal.rss_url, journal.title, journal.publisher)
    except Exception as e:
        print(f"  [{journal.publisher}] {journal.title} error: {e}")
        return []


def collect_all_journals(limit: int = 20, timeout: int = 120) -> List[RSSPaper]:
    """
    从数据库读取所有活跃期刊，采集RSS
    """
    db = SessionLocal()
    try:
        journals = db.query(Journal).filter(Journal.is_active == True).all()
    finally:
        db.close()

    journals = [j for j in journals if j.rss_url]
    # Non-ACS journals first (faster HTTP RSS)
    journals.sort(key=lambda j: j.publisher == "ACS")

    all_papers = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_one, j, limit): j for j in journals}
        for future in as_completed(futures, timeout=timeout):
            papers = future.result()
            all_papers.extend(papers[:limit])

    return all_papers


# ==========================================================
# 向后兼容：保留原来的 collector.py 接口
# ==========================================================
def collect_all(limit: int = 20) -> List[RSSPaper]:
    return collect_all_journals(limit)


if __name__ == "__main__":
    print("=" * 60)
    print("Testing RSS Collector (from database)...")
    print("=" * 60)
    papers = collect_all_journals(limit=5)
    print(f"\nCollected {len(papers)} papers")
    for p in papers[:10]:
        print(f"  - [{p.source}] {p.title[:60]}")
