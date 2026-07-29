"""
RSS 采集器 - 从数据库读取期刊列表，统一采集所有活跃期刊的RSS源

使用 cloudscraper 绕过 Cloudflare，支持：
- ACS / Science / Wiley（cloudscraper 自动处理）
- RSC / Nature / Elsevier / Springer
"""
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from bs4 import BeautifulSoup
import feedparser
import cloudscraper

from database.database import SessionLocal
from database.models import Journal
from services.models.rss_paper import RSSPaper
from services.discovery.rss_normalizer import clean_html, clean_spaces, extract_doi, remove_doi, remove_metadata

_scraper = cloudscraper.create_scraper()


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


def fetch_rss(url: str, journal: str, publisher: str) -> List[RSSPaper]:
    papers = []
    try:
        r = _scraper.get(url, timeout=30)
        if r.status_code != 200:
            return papers
        feed = feedparser.parse(r.text)
        for entry in feed.entries:
            paper = normalize_entry(entry, source=publisher, journal_title=journal, publisher=publisher)
            if paper:
                papers.append(paper)
    except Exception:
        pass
    return papers


def _fetch_one(journal, limit):
    return fetch_rss(journal.rss_url, journal.title, journal.publisher)


def collect_all_journals(limit: int = 20, timeout: int = 120) -> List[RSSPaper]:
    db = SessionLocal()
    try:
        journals = db.query(Journal).filter(Journal.is_active == True).all()
    finally:
        db.close()

    journals = [j for j in journals if j.rss_url]
    all_papers = []
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(_fetch_one, j, limit): j for j in journals}
        for future in as_completed(futures, timeout=timeout):
            papers = future.result()
            all_papers.extend(papers[:limit])
    return all_papers


# 向后兼容
def collect_all(limit: int = 20) -> List[RSSPaper]:
    return collect_all_journals(limit)


if __name__ == "__main__":
    print("=" * 60)
    print("Testing RSS Collector...")
    print("=" * 60)
    papers = collect_all_journals(limit=5)
    print(f"\nCollected {len(papers)} papers")
    for p in papers[:10]:
        print(f"  - [{p.source}] {p.title[:60]}")
