from typing import List

from services.models.rss_paper import RSSPaper

from services.sources.rss.nature import fetch_nature
from services.sources.rss.acs import fetch_acs


# ==========================================================
# Registered RSS Sources
# ==========================================================

RSS_SOURCES = [

    fetch_nature,

    fetch_acs,

]


# ==========================================================
# Collect All RSS Papers
# ==========================================================

def collect_all(

    limit: int = 20

) -> List[RSSPaper]:

    papers = []

    for source in RSS_SOURCES:

        try:

            papers.extend(

                source(limit)

            )

        except Exception as e:

            print(

                f"[RSS ERROR] {source.__name__}: {e}"

            )

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