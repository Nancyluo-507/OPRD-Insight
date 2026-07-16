import feedparser

from typing import List

from services.models.rss_paper import RSSPaper
from services.discovery.rss_normalizer import normalize_entry


# ==========================================================
# Universal RSS Parser
# ==========================================================

def fetch_feed(

    rss_url: str,

    source: str,

    limit: int = 20

) -> List[RSSPaper]:

    feed = feedparser.parse(

        rss_url

    )

    if feed.bozo:

        raise RuntimeError(

            f"Failed to parse RSS: {rss_url}"

        )

    papers: List[RSSPaper] = []

    entries = feed.entries[:limit]

    for entry in entries:

        try:

            paper = normalize_entry(

                entry,

                source

            )

            papers.append(

                paper

            )

        except Exception as e:

            print(

                f"[Normalize Error] {source}: {e}"

            )

            continue

    return papers


# ==========================================================
# Fetch Without Limit
# ==========================================================

def fetch_all(

    rss_url: str,

    source: str

) -> List[RSSPaper]:

    return fetch_feed(

        rss_url=rss_url,

        source=source,

        limit=100000

    )