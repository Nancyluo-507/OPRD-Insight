from datetime import datetime

from services.core.semantic_match import (
    expand_query,
    semantic_match
)

from services.core.embedding_match import embedding_score

from services.models.paper import Paper


CURRENT_YEAR = datetime.now().year


# ==========================================================
# Calculate Score
# ==========================================================

def calculate_score(

    query: str,

    paper: Paper

) -> float:

    score = 0

    matched_keywords = semantic_match(

        query,

        " ".join(

            [

                paper.title,

                paper.abstract,

                paper.journal,

                " ".join(

                    paper.keywords

                ),

                " ".join(

                    paper.subjects

                )

            ]

        )

    )

    paper.matched_keywords = matched_keywords

    expanded_keywords = expand_query(

        query

    )
    # ======================================================
    # Semantic Match
    # ======================================================

    title = paper.title.lower()

    abstract = paper.abstract.lower()

    journal = paper.journal.lower()

    keywords = " ".join(

        paper.keywords

    ).lower()

    subjects = " ".join(

        paper.subjects

    ).lower()

    for word in expanded_keywords:

        word = word.lower()

        if word in title:

            score += 40

        if word in keywords:

            score += 25

        if word in subjects:

            score += 20

        if word in abstract:

            score += 15

        if word in journal:

            score += 5
    # ======================================================
    # Citation
    # ======================================================

    score += min(

        paper.citation / 50,

        20

    )

    # ======================================================
    # Open Access
    # ======================================================

    if paper.is_open_access:

        score += 3

    # ======================================================
    # Recent Paper
    # ======================================================

    if paper.year:

        if paper.year >= CURRENT_YEAR - 1:

            score += 30

        elif paper.year >= CURRENT_YEAR - 3:

            score += 20

        elif paper.year >= CURRENT_YEAR - 5:

            score += 10
    # ======================================================
    # Semantic Bonus
    # ======================================================

    score += len(

        matched_keywords

    ) * 2

    # ======================================================
    # Embedding Similarity (sentence-transformers)
    # ======================================================

    score += embedding_score(

        query,

        paper.title,

        paper.abstract,

        use_transformer=True

    )

    return round(

        score,

        2

    )
# ==========================================================
# Rank Papers
# ==========================================================

def rank_papers(

    papers,

    query

):

    for paper in papers:

        paper.score = calculate_score(

            query,

            paper

        )

    papers.sort(

        key=lambda x: x.score,

        reverse=True

    )

    return papers


if __name__ == "__main__":

    paper = Paper(

        title="Nickel single atom catalyst for CO2 reduction",

        abstract="Metal organic framework derived catalyst.",

        journal="Nature Catalysis",

        keywords=[

            "Nickel",

            "MOF",

            "CO2"

        ],

        subjects=[

            "Electrocatalysis"

        ],

        citation=865,

        year=CURRENT_YEAR,

        is_open_access=True

    )

    print(

        calculate_score(

            "nickel MOF CO2",

            paper

        )

    )

    print()

    print(

        paper.matched_keywords

    )