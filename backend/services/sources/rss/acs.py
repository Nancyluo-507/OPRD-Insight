from .base import fetch_feed


# ==========================================================
# ACS RSS
# ==========================================================

RSS_URL = "https://pubs.acs.org/action/showFeed?type=etoc&jc=jacsat"


# ==========================================================
# Fetch
# ==========================================================

def fetch_acs(

    limit: int = 20

):

    return fetch_feed(

        RSS_URL,

        "ACS",

        limit

    )


# ==========================================================
# Test
# ==========================================================

if __name__ == "__main__":

    papers = fetch_acs()

    print()

    print(f"Found {len(papers)} papers")

    print()

    for index, paper in enumerate(

        papers,

        start=1

    ):

        print(index)

        print(paper.title)

        print(paper.published)

        print(paper.url)

        print("-" * 80)