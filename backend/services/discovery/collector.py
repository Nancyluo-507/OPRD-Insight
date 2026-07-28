from typing import List

from services.models.rss_paper import RSSPaper

from services.sources.rss.collector import collect_all_journals


# ==========================================================
# Collect All RSS Papers (from all 59 journals in DB)
# ==========================================================

def collect_all(

    limit: int = 20

) -> List[RSSPaper]:

    papers = collect_all_journals(limit=limit, timeout=120)

    if papers:
        print("=" * 80)
        print(type(papers[0]))
        print(vars(papers[0]))
        print("=" * 80)

    return papers


# ==========================================================
# Test
# ==========================================================

if __name__ == "__main__":

    papers = collect_all()

    print()

    print("=" * 60)

    print(

        f"Collected {len(papers)} papers"

    )

    print("=" * 60)

    print()

    for index, paper in enumerate(

        papers,

        start=1

    ):

        print(index)

        print(paper.source)

        print(paper.title)

        print(paper.published)

        print(paper.url)

        print("-" * 80)