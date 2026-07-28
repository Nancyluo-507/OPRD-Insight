"""
CrossRef 数据源 - 优化版

特性：
- polite pool：mailto + User-Agent
- 请求间隔控制 + 自动重试 + 指数退避
- 支持增量抓取（from-created-date）
- 支持按 ISSN 精准过滤
- 兼容原有 search_crossref 接口
"""
import time
import random
from datetime import datetime, timedelta
import requests
from typing import List, Tuple, Optional

from services.models.paper import Paper
from services.parsers.crossref_parser import normalize_crossref_paper, parse_abstract


# ==========================================================
# 配置
# ==========================================================
CROSSREF_URL = "https://api.crossref.org/works"
CONTACT_EMAIL = "nancy@boehringer-ingelheim.com"  # polite pool 邮箱
DEFAULT_PER_PAGE = 100
TIMEOUT = 30
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1.0  # 秒
MIN_INTERVAL = 0.2  # 请求最小间隔（200ms，进入polite pool）

# 请求追踪 - 控制请求间隔
_last_request_time = 0.0


def _wait_for_polite_pool():
    """请求间隔控制，确保进入CrossRef polite pool"""
    global _last_request_time
    now = time.time()
    elapsed = now - _last_request_time
    if elapsed < MIN_INTERVAL:
        time.sleep(MIN_INTERVAL - elapsed)
    _last_request_time = time.time()


def _build_headers() -> dict:
    """构造 polite pool 请求头"""
    return {
        "User-Agent": f"ChemVigil/1.0 (mailto:{CONTACT_EMAIL})",
    }


def _should_retry(status_code: int) -> bool:
    """判断是否需要重试"""
    if status_code == 429:  # Too Many Requests
        return True
    if status_code >= 500:  # Server Error
        return True
    return False


def request_crossref(
    query: str = "",
    issn: str = "",
    offset: int = 0,
    rows: int = DEFAULT_PER_PAGE,
    from_date: str = "",
    sort: str = "relevance",
) -> Tuple[List[dict], int]:
    """
    请求 CrossRef API
    Args:
        query: 搜索关键词
        issn: ISSN 号（按期刊过滤）
        offset: 分页偏移
        rows: 每页数量
        from_date: 起始日期 (YYYY-MM-DD)
        sort: 排序方式 (relevance / created)
    Returns:
        (items, total_count)
    """
    params = {
        "query": query,
        "rows": min(rows, 100),
        "offset": offset,
        "sort": sort,
        "order": "desc",
        "mailto": CONTACT_EMAIL,
    }

    # 如果指定了 ISSN，添加到 filter
    filters = []
    if issn:
        filters.append(f"issn:{issn}")
    if from_date:
        filters.append(f"from-created-date:{from_date}")
    if filters:
        params["filter"] = ",".join(filters)

    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            _wait_for_polite_pool()
            response = requests.get(
                CROSSREF_URL,
                params=params,
                headers=_build_headers(),
                timeout=TIMEOUT,
            )
            if response.status_code == 200:
                data = response.json()
                message = data.get("message", {})
                total_count = message.get("total-results", 0)
                items = message.get("items", [])
                return items, total_count
            elif _should_retry(response.status_code) and attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** attempt) + random.uniform(0, 0.5)
                print(f"  CrossRef retry {attempt + 1}/{MAX_RETRIES} (status={response.status_code}, delay={delay:.1f}s)")
                time.sleep(delay)
                last_error = f"HTTP {response.status_code}"
            else:
                print(f"  CrossRef error: HTTP {response.status_code}")
                return [], 0
        except requests.exceptions.Timeout:
            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                print(f"  CrossRef timeout, retry {attempt + 1}/{MAX_RETRIES} (delay={delay:.1f}s)")
                time.sleep(delay)
                last_error = "Timeout"
            else:
                print(f"  CrossRef timeout after {MAX_RETRIES} retries")
                return [], 0
        except Exception as e:
            print(f"  CrossRef request error: {e}")
            return [], 0

    print(f"  CrossRef failed after retries: {last_error}")
    return [], 0


def fetch_articles_by_issn(
    issn: str,
    from_date: Optional[datetime] = None,
    per_page: int = 100,
) -> Tuple[List[Paper], int]:
    """
    按 ISSN 精准抓取期刊文章（增量模式）
    Args:
        issn: ISSN 号
        from_date: 起始日期，None则抓取最近30天
        per_page: 每页数量
    Returns:
        (papers, total_count)
    """
    date_str = ""
    if from_date:
        date_str = from_date.strftime("%Y-%m-%d")
    else:
        date_str = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

    items, total = request_crossref(
        query="",
        issn=issn,
        rows=per_page,
        from_date=date_str,
    )

    papers = []
    for item in items:
        try:
            paper = normalize_crossref_paper(item)
            if paper.doi:
                papers.append(paper)
        except Exception as e:
            print(f"  Parse error: {e}")
            continue

    return papers, total


# ==========================================================
# 兼容原有接口
# ==========================================================
def search_crossref(
    query: str,
    cursor="*",
    per_page: int = 50,
) -> Tuple[List[Paper], None, int]:
    """
    原有 search_crossref 接口（按关键词搜索）
    保持与之前完全相同的参数和返回值
    """
    items, total_count = request_crossref(
        query=query,
        rows=per_page,
        sort="relevance",
    )

    papers = []
    for item in items:
        try:
            paper = normalize_crossref_paper(item)
            papers.append(paper)
        except Exception as e:
            print(f"CrossRef Parser Error: {e}")
            continue

    return papers, None, total_count


# ==========================================================
# DOI 信息查询（摘要回填）
# ==========================================================

def resolve_doi(doi: str) -> dict:
    """
    通过 CrossRef API 查询单篇 DOI 的元数据
    返回 {title, abstract, authors, journal, publisher} 或 None
    """
    from services.discovery.rss_normalizer import clean_html
    url = f"{CROSSREF_URL}/{doi}"
    try:
        _wait_for_polite_pool()
        resp = requests.get(url, headers=_build_headers(), timeout=TIMEOUT)
        if resp.status_code != 200:
            return None
        data = resp.json()
        msg = data.get("message", {})
        abstract = parse_abstract(msg)
        if abstract:
            abstract = clean_html(abstract)
        return {
            "doi": doi,
            "abstract": abstract,
        }
    except Exception as e:
        print(f"  resolve_doi({doi}): {e}")
        return None


def resolve_doi_openalex(doi: str) -> dict:
    """
    通过 OpenAlex API 查询单篇 DOI 的摘要
    OpenAlex 对 ACS 等出版社覆盖较好
    """
    from services.parsers.paper_parser import parse_abstract as parse_oa_abstract
    url = f"https://api.openalex.org/works/doi:{doi}"
    try:
        resp = requests.get(url, headers={"User-Agent": "ChemVigil/1.0"}, timeout=10)
        if resp.status_code != 200:
            return None
        data = resp.json()
        inv_index = data.get("abstract_inverted_index")
        abstract = parse_oa_abstract(inv_index or {})
        if abstract:
            return {"doi": doi, "abstract": abstract}
        return None
    except Exception as e:
        print(f"  openalex({doi}): {e}")
        return None


def resolve_doi_any(doi: str) -> dict:
    """Try CrossRef first, fallback to OpenAlex"""
    result = resolve_doi(doi)
    if result and result.get("abstract"):
        return result
    return resolve_doi_openalex(doi)


def batch_enrich_abstracts(dois: list, max_workers: int = 3, source: str = "crossref") -> dict:
    """
    批量通过 DOI 查询摘要，返回 {doi: abstract} 映射
    控制并发数避免触发 CrossRef 限流
    source: "crossref" | "openalex" | "any"
    """
    import concurrent.futures
    resolver = {"crossref": resolve_doi, "openalex": resolve_doi_openalex, "any": resolve_doi_any}.get(source, resolve_doi)
    result = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
        fut_map = {pool.submit(resolver, d): d for d in dois}
        for fut in concurrent.futures.as_completed(fut_map):
            info = fut.result()
            if info and info.get("abstract"):
                result[info["doi"]] = info["abstract"]
    return result


def batch_enrich_all_sources(dois: list, max_workers: int = 3) -> dict:
    """Enrich with CrossRef first, then fallback to OpenAlex for missing DOIs"""
    result = batch_enrich_abstracts(dois, max_workers, source="crossref")
    missing = [d for d in dois if d not in result]
    if missing:
        print(f"  CrossRef gave {len(result)} abstracts, trying OpenAlex for {len(missing)} remaining...")
        oa_result = batch_enrich_abstracts(missing, max_workers, source="openalex")
        result.update(oa_result)
    return result


if __name__ == "__main__":
    # 测试：按关键词搜索
    papers, _, total = search_crossref("metal organic framework", per_page=3)
    print(f"Search: {len(papers)} papers (total={total})")
    for p in papers[:3]:
        print(f"  {p.title[:60]}")

    # 测试：按 ISSN 增量抓取（OPRD）
    print("\n--- Fetch by ISSN (OPRD: 1083-6160) ---")
    papers, total = fetch_articles_by_issn("1083-6160", per_page=3)
    print(f"  {len(papers)} papers (total={total})")
    for p in papers[:3]:
        print(f"  {p.title[:60]}")

    # 测试：单 DOI 查询
    print("\n--- DOI resolve ---")
    info = resolve_doi("10.1038/s41929-026-01592-x")
    print(f"  abstract: {(info or {}).get('abstract', 'N/A')[:120]}")
