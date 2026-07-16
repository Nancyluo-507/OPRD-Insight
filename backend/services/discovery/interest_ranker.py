from typing import List

from services.models.paper import Paper
from services.models.rss_paper import RSSPaper


# ==========================================================
# Score One Item
# ==========================================================

def score_item(

    item,

    interests: List[str]

) -> int:

    score = 0

    text = ""

    if hasattr(item, "title"):

        text += item.title.lower()

    if hasattr(item, "abstract"):

        text += " " + (item.abstract or "").lower()

    if hasattr(item, "summary"):

        text += " " + (item.summary or "").lower()

    for keyword in interests:

        if keyword.lower() in text:

            score += 1

    return score
# ==========================================================
# Rank
# ==========================================================

def rank_items(

    items,

    interests: List[str]

):

    scored = []

    for item in items:

        score = score_item(

            item,

            interests

        )

        scored.append(

            (

                score,

                item

            )

        )

    scored.sort(

        key=lambda x: x[0],

        reverse=True

    )

    return [

        item

        for _, item in scored

    ]