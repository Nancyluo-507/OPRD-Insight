import requests

from typing import List

from services.models.paper import Paper

from services.core.query_processor import process_query
from services.core.semantic_score import rank_papers
from services.core.highlight import highlight_paper

from services.parsers.paper_parser import (
    normalize_openalex_paper
)


# ==========================================================
# Config
# ==========================================================

OPENALEX_URL = "https://api.openalex.org/works"

DEFAULT_PER_PAGE = 25

TIMEOUT = 30


session = requests.Session()

session.headers.update(

    {

        "User-Agent":

        "OPRD-Insight/1.0"

    }

)


# ==========================================================
# Request
# ==========================================================

def request_openalex(

    search_query: str,

    cursor: str = "*",

    per_page: int = DEFAULT_PER_PAGE

):

    response = session.get(

        OPENALEX_URL,

        params={

            "search": search_query,

            "per-page": per_page,

            "cursor": cursor

        },

        timeout=TIMEOUT

    )

    response.raise_for_status()

    data = response.json()

    next_cursor = (

        data

        .get("meta", {})

        .get("next_cursor")

    )

    total_count = (

        data

        .get("meta", {})

        .get("count", 0)

    )

    return (

        data,

        next_cursor,

        total_count

    )
# ==========================================================
# Search
# ==========================================================

def search_openalex(

    query: str,

    cursor: str = "*",

    per_page: int = DEFAULT_PER_PAGE

):

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