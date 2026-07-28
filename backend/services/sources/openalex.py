import time
import random
import requests

from typing import List

from services.models.paper import Paper

from services.core.query_processor import process_query
from services.core.semantic_score import rank_papers
from services.core.highlight import highlight_paper

from services.parsers.paper_parser import (
    normalize_openalex_paper
)

from config.settings import settings


session = requests.Session()

session.headers.update(

    {

        "User-Agent": settings.OPENALEX_USER_AGENT

    }

)


# ==========================================================
# Request
# ==========================================================

def request_openalex(

    search_query: str,

    cursor: str = "*",

    per_page: int = None

):

    if per_page is None:
        per_page = settings.OPENALEX_PER_PAGE

    max_retries = 3
    last_error = None
    for attempt in range(max_retries + 1):
        try:
            response = session.get(

                settings.OPENALEX_URL,

                params={

                    "search": search_query,

                    "per-page": per_page,

                    "cursor": cursor

                },

                timeout=settings.OPENALEX_TIMEOUT

            )

            if response.status_code == 200:
                data = response.json()
                next_cursor = data.get("meta", {}).get("next_cursor")
                total_count = data.get("meta", {}).get("count", 0)
                return data, next_cursor, total_count

            last_error = f"HTTP {response.status_code}"
            if response.status_code in (429, 502, 503, 504) and attempt < max_retries:
                delay = 1.0 * (2 ** attempt) + random.uniform(0, 0.5)
                print(f"  OpenAlex retry {attempt+1}/{max_retries} ({last_error}, delay={delay:.1f}s)")
                time.sleep(delay)
                continue

            print(f"OpenAlex error: {last_error}")
            return {"meta": {"next_cursor": None, "count": 0}, "results": []}, None, 0

        except requests.exceptions.Timeout:
            if attempt < max_retries:
                delay = 1.0 * (2 ** attempt) + random.uniform(0, 0.5)
                print(f"  OpenAlex timeout, retry {attempt+1}/{max_retries} (delay={delay:.1f}s)")
                time.sleep(delay)
                last_error = "Timeout"
            else:
                print(f"  OpenAlex timeout after {max_retries} retries")
                return {"meta": {"next_cursor": None, "count": 0}, "results": []}, None, 0
        except Exception as e:
            print(f"OpenAlex request failed: {e}")
            return {"meta": {"next_cursor": None, "count": 0}, "results": []}, None, 0
# ==========================================================
# Search
# ==========================================================

def search_openalex(

    query: str,

    cursor: str = "*",

    per_page: int = None

):

    if per_page is None:
        per_page = settings.OPENALEX_PER_PAGE

    query_info = process_query(

        query

    )

    search_query = query_info[

        "search_query"

    ]

    data, next_cursor, total_count = request_openalex(

        search_query=search_query,

        cursor=cursor,

        per_page=per_page

    )

    works = data.get(

        "results",

        []

    )

    papers = []

    # ======================================================
    # Parse OpenAlex Papers
    # ======================================================

    for work in works:

        try:

            paper = normalize_openalex_paper(

                work

            )

            papers.append(

                paper

            )

        except Exception as e:

            print(

                f"Parser Error: {e}"

            )

            continue

    # ======================================================
    # Semantic Ranking
    # ======================================================

    papers = rank_papers(

        papers,

        query

    )

    # ======================================================
    # Highlight
    # ======================================================

    result = []

    for paper in papers:

        result.append(

            highlight_paper(

                paper,

                query

            )

        )

    return (

        result,

        next_cursor,

        total_count

    )