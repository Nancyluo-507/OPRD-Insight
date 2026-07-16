from .base import fetch_feed


RSS_URL = "https://www.nature.com/nature.rss"


def fetch_nature(

    limit: int = 20

):

    return fetch_feed(

        RSS_URL,

        "Nature",

        limit

    )


if __name__ == "__main__":

    papers = fetch_nature()

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