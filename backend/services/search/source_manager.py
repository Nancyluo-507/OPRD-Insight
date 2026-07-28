# ==========================================================
# ChemVigil Source Manager
# ==========================================================

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from services.config.sources import SEARCH_SOURCES

from services.core.deduplicate import deduplicate_papers

from services.core.semantic_score import rank_papers

from services.core.highlight import highlight_paper

from services.core.chemistry_filter import is_chemistry_related


LOCAL_SOURCE_NAMES = {"local_db"}  # 仅作为离线回退


# ==========================================================
# Search All Sources (Parallel)
# ==========================================================

def _parse_pub_date(date_str: str):
    """Parse publication_date string to datetime, return None if unparseable."""
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m", "%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date_str.strip(), fmt)
        except ValueError:
            continue
    return None

def _compute_cutoff(time_range: str) -> datetime | None:
    if time_range in ("all", "", None):
        return None
    days_map = {"1w": 7, "1m": 30, "3m": 90, "1y": 365}
    days = days_map.get(time_range)
    if days is None:
        return None
    return datetime.now() - timedelta(days=days)


def search_all_sources(

    query: str,

    per_source: int = 50,

    cursors: dict = None,

    time_range: str = "all",

):


    t_start = time.perf_counter()

    all_papers = []

    total_count = 0

    cursors = dict(cursors or {})

    remote_ok = False


    def search_one(name, source, cursor_val):

        if not source["enabled"]:

            return name, [], None, 0

        try:

            result = source["handler"](

                query,

                cursor=cursor_val,

                per_page=per_source

            )

            papers = result[0]

            next_cursor = result[1]

            count = result[2]

            print(name, "returned:", len(papers), "cursor:", cursor_val)

            return name, papers, next_cursor, count

        except Exception as e:

            print(f"{name} search error:", e)

            return name, [], None, 0



    with ThreadPoolExecutor(max_workers=len(SEARCH_SOURCES)) as executor:

        futures = {
            executor.submit(search_one, name, source, cursors.get(name, "*")): name
            for name, source in SEARCH_SOURCES.items()
            if source["enabled"]
        }

        for future in as_completed(futures):
            name, papers, next_cursor, count = future.result()
            if name not in LOCAL_SOURCE_NAMES and papers:
                remote_ok = True
            all_papers.extend(papers)
            total_count += count
            cursors[name] = next_cursor

    # 如果远程 API 全部失败（断网），回退到本地数据库
    if not remote_ok:
        local_source = SEARCH_SOURCES.get("local_db")
        if local_source and local_source["enabled"]:
            print("Remote APIs unreachable, falling back to local DB")
            try:
                local_result = local_source["handler"](query, cursor="*", per_page=per_source)
                local_papers = local_result[0] if local_result else []
                all_papers = local_papers
                total_count = len(local_papers)
                cursors = {"local_db": None}
            except Exception as e:
                print("Local DB fallback error:", e)
                all_papers = []

    t_fetch = int((time.perf_counter() - t_start) * 1000)
    print(f"[Timing] Fetch: {t_fetch}ms | papers={len(all_papers)}")

    # ======================================================
    # Deduplicate
    # ======================================================

    before_count = len(all_papers)
    t0 = time.perf_counter()
    all_papers = deduplicate_papers(all_papers)
    t_dedup = int((time.perf_counter() - t0) * 1000)
    print(f"[Timing] Deduplicate: {t_dedup}ms | {before_count} -> {len(all_papers)}")

    # ======================================================
    # Time Filter
    # ======================================================

    cutoff = _compute_cutoff(time_range)
    if cutoff is not None:
        before = len(all_papers)
        t0 = time.perf_counter()
        filtered = []
        for p in all_papers:
            dt = _parse_pub_date(p.publication_date)
            if dt is not None and dt >= cutoff:
                filtered.append(p)
        all_papers = filtered
        t_filter = int((time.perf_counter() - t0) * 1000)
        print(f"[Timing] TimeFilter: {t_filter}ms | {before} -> {len(all_papers)}")

    # ======================================================
    # Unified Ranking
    # ======================================================

    t0 = time.perf_counter()
    all_papers = rank_papers(all_papers, query)
    t_rank = int((time.perf_counter() - t0) * 1000)
    print(f"[Timing] Rank: {t_rank}ms | papers={len(all_papers)}")

    # ======================================================
    # Chemistry Relevance Filter
    # ======================================================

    before_filter = len(all_papers)
    t0 = time.perf_counter()
    all_papers = [p for p in all_papers if p.score >= 10 and is_chemistry_related(p, query)]
    t_filter_chem = int((time.perf_counter() - t0) * 1000)
    print(f"[Timing] ChemFilter: {t_filter_chem}ms | {before_filter} -> {len(all_papers)}")

    # ======================================================
    # Highlight
    # ======================================================

    t0 = time.perf_counter()
    highlighted = []
    for paper in all_papers:
        highlighted.append(highlight_paper(paper, query))
    all_papers = highlighted
    t_highlight = int((time.perf_counter() - t0) * 1000)
    print(f"[Timing] Highlight: {t_highlight}ms | papers={len(all_papers)}")

    t_total = int((time.perf_counter() - t_start) * 1000)
    print(f"[Timing] TOTAL: {t_total}ms")

    return {

        "papers": all_papers,

        "total_count": total_count,

        "cursors": cursors,

    }