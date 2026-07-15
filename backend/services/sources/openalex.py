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

    per_page: int = DEFAULT_PER_PAGE

):

    response = session.get(

        OPENALEX_URL,

        params={

            "search": search_query,

            "per-page": per_page

        },

        timeout=TIMEOUT

    )

    response.raise_for_status()

    return response.json()


# ==========================================================
# Search
# ==========================================================

def search_openalex(

    query: str,

    per_page: int = DEFAULT_PER_PAGE

) -> List[Paper]:

    query_info = process_query(

        query

    )

    search_query = query_info[

        "search_query"

    ]

    data = request_openalex(

        search_query,

        per_page

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

    return result
# ==========================================================
# Main
# ==========================================================

if __name__ == "__main__":

    print()

    print("=" * 60)

    print("OpenAlex Search Test")

    print("=" * 60)

    print()

    query = input(

        "Please enter your query: "

    ).strip()

    if not query:

        print()

        print("Query cannot be empty.")

        exit()

    try:

        papers = search_openalex(

            query

        )
        print(type(papers))
        print(len(papers))
        print(type(papers[0]))

    except requests.exceptions.RequestException as e:

        print()

        print("Network Error:")

        print(e)

        exit()

    except Exception as e:

        print()

        print("Search Error:")

        print(e)

        exit()

    print()

    print("=" * 60)

    print(f"Found {len(papers)} papers")

    print("=" * 60)

    print()

    for index, paper in enumerate(

        papers,

        start=1

    ):

        print(f"[{index}]")

        print(f"Score      : {paper.score}")

        print(f"Title      : {paper.title}")

        print(f"Authors    : {paper.authors}")

        print(f"Journal    : {paper.journal}")

        print(f"Year       : {paper.year}")

        print(f"Citations  : {paper.citation}")

        print(f"DOI        : {paper.doi}")

        print(f"DOI URL    : {paper.doi_url}")

        print(f"PDF URL    : {paper.pdf_url}")

        print(f"Open Access: {paper.is_open_access}")

        if paper.matched_keywords:

            print(

                "Matched    :",

                ", ".join(

                    paper.matched_keywords

                )

            )

        print("-" * 60)

    print()

    print("Finished.")