from typing import Optional

from services.models.rss_paper import RSSPaper
from services.models.paper import Paper

from services.sources.openalex import search_openalex


# ==========================================================
# Enrich One RSS Paper
# ==========================================================

def enrich_paper(rss_paper: RSSPaper):

    try:
        papers, _, _ = search_openalex(
            rss_paper.title,
            per_page=1
        )

    except Exception:
        return None

    if len(papers) == 0:
        return None

    return papers[0]
# ==========================================================
# Enrich All RSS Papers
# ==========================================================

def enrich_all(rss_papers):

    enriched = []
    failed = []

    for rss_paper in rss_papers:

        paper = enrich_paper(rss_paper)

        if paper is None:
            print("[RSS ONLY]", rss_paper.title)
            failed.append(rss_paper)

        else:
            print("[ENRICHED]", type(paper), paper.title)
            enriched.append(paper)

    return {
        "papers": enriched,
        "rss_only": failed
    }
# ==========================================================
# Test
# ==========================================================

if __name__ == "__main__":

    from services.discovery.collector import collect_all

    rss_papers = collect_all(

        limit=5

    )

    result = enrich_all(

        rss_papers

    )

    print()

    print("=" * 60)

    print(

        "Enriched:",

        len(result["papers"])

    )

    print(

        "RSS Only:",

        len(result["rss_only"])

    )

    print("=" * 60)

    print()

    for paper in result["papers"]:

        print(

            "[OpenAlex]"

        )

        print(

            paper.title

        )

        print(

            paper.authors

        )

        print("-" * 60)

    for paper in result["rss_only"]:

        print(

            "[RSS]"

        )

        print(

            paper.title

        )

        print("-" * 60)