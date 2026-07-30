"""
RSS 采集器 - 从数据库读取期刊列表，统一采集所有活跃期刊的RSS源

流程：
- ACS → 有 browser-act 用 browser-act，没有则跳过（论文走搜索API）
- 其他出版社 → cloudscraper（自动处理 Cloudflare / 直连）
"""
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List
from bs4 import BeautifulSoup
import feedparser
import cloudscraper

from database.database import SessionLocal
from database.models import Journal
from services.models.rss_paper import RSSPaper
from services.discovery.rss_normalizer import clean_html, clean_spaces, extract_doi, remove_doi, remove_metadata


def _get_scraper():
    if not hasattr(_get_scraper, "_instance"):
        _get_scraper._instance = cloudscraper.create_scraper()
    return _get_scraper._instance

BROWSER_ACT = r"C:\Users\luoyihan\.local\bin\browser-act.exe"
_SESSION = "acs-batch"
_BROWSER_OPENED = False
_BROWSER_ID = "108290830888227166"


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
    if not authors_list:
        atom_authors = entry.get("authors", [])
        if atom_authors:
            authors_list = [a.get("name", str(a)) for a in atom_authors if hasattr(a, "get")]

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


# ========== browser-act (ACS Cloudflare 绕过，仅 Windows) ==========

def _ensure_browser():
    global _BROWSER_OPENED
    if _BROWSER_OPENED:
        return True
    import subprocess
    try:
        r = subprocess.run([BROWSER_ACT, "--session", _SESSION, "browser", "open",
                           _BROWSER_ID, "about:blank"], capture_output=True, timeout=30)
        if r.returncode == 0:
            _BROWSER_OPENED = True
            return True
        return False
    except Exception:
        return False


def _fetch_acs_browser(url: str, journal: str, publisher: str) -> List[RSSPaper]:
    if not _ensure_browser():
        return []
    import subprocess
    papers = []
    try:
        r = subprocess.run([BROWSER_ACT, "--session", _SESSION, "navigate", url],
                           capture_output=True, timeout=15)
        if r.returncode != 0:
            return papers
        time.sleep(2)
        r2 = subprocess.run([BROWSER_ACT, "--session", _SESSION, "get", "markdown"],
                            capture_output=True, timeout=10)
        if r2.returncode != 0:
            return papers
        content = r2.stdout.decode("utf-8", errors="replace")
        idx = content.find("The document tree is shown below.")
        xml_text = content[idx + len("The document tree is shown below."):].strip() if idx > 0 else content
        soup = BeautifulSoup(xml_text, "xml")
        for item in soup.find_all("item"):
            paper = normalize_entry(
                {"title": item.find("title"), "link": item.find("link"),
                 "pubDate": item.find("pubDate"), "summary": item.find("description") or item.find("summary"),
                 "abstract": item.find("abstract")},
                source="ACS", journal_title=journal, publisher=publisher
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
    except Exception:
        pass
    return papers


# ========== cloudscraper (非 ACS 出版社) ==========

def _fetch_scraper(url: str, journal: str, publisher: str) -> List[RSSPaper]:
    papers = []
    try:
        r = _get_scraper().get(url, timeout=30)
        if r.status_code != 200:
            print(f"  RSS {journal}: HTTP {r.status_code}")
            return papers
        feed = feedparser.parse(r.text)
        for entry in feed.entries:
            paper = normalize_entry(entry, source=publisher, journal_title=journal, publisher=publisher)
            if paper:
                papers.append(paper)
        if not papers:
            print(f"  RSS {journal}: 0 entries parsed from feed")
        else:
            print(f"  RSS {journal}: {len(papers)} papers")
    except Exception as e:
        print(f"  RSS {journal} error: {e}")
    return papers


# ========== 分发 ==========

def _fetch_one(journal, limit):
    if journal.publisher == "ACS":
        return _fetch_acs_browser(journal.rss_url, journal.title, journal.publisher)
    return _fetch_scraper(journal.rss_url, journal.title, journal.publisher)


def collect_all_journals(limit: int = 20, timeout: int = 120) -> List[RSSPaper]:
    db = SessionLocal()
    try:
        journals = db.query(Journal).filter(Journal.is_active == True).all()
    finally:
        db.close()

    journals = [j for j in journals if j.rss_url]
    journals.sort(key=lambda j: j.publisher == "ACS")
    all_papers = []
    with ThreadPoolExecutor(max_workers=16) as pool:
        futures = {pool.submit(_fetch_one, j, limit): j for j in journals}
        for future in as_completed(futures, timeout=timeout):
            papers = future.result()
            all_papers.extend(papers[:limit])
    return all_papers


def collect_all(limit: int = 20) -> List[RSSPaper]:
    return collect_all_journals(limit)


if __name__ == "__main__":
    papers = collect_all_journals(limit=5)
    print(f"Collected {len(papers)} papers")
