# ==========================================================
# ChemVigil Quality Filter
# ==========================================================


BAD_TYPES = [

    "reference-entry",

    "dataset",

    "component",

    "standard",

    "report"

]



# ==========================================================
# Basic Check
# ==========================================================

def basic_quality_check(

    paper

):


    # --------------------------
    # Title
    # --------------------------

    if not paper.title:

        return False



    # --------------------------
    # Bad Source Types
    # --------------------------

    source_type = getattr(

        paper,

        "type",

        ""

    )


    if source_type in BAD_TYPES:

        return False



    return True



# ==========================================================
# Quality Score
# ==========================================================

def calculate_quality_score(

    paper

):


    score = 100



    # --------------------------
    # Abstract
    # --------------------------

    if not paper.abstract:

        score -= 20



    # --------------------------
    # Authors
    # --------------------------

    if not paper.authors:

        score -= 15



    # --------------------------
    # DOI
    # --------------------------

    if not paper.doi:

        score -= 10



    # --------------------------
    # Citation
    # --------------------------

    if paper.citation:

        if paper.citation > 100:

            score += 5



    if score < 0:

        score = 0



    return score



# ==========================================================
# Filter Papers
# ==========================================================

def filter_quality(

    papers

):


    results = []



    for paper in papers:


        if not basic_quality_check(

            paper

        ):

            continue



        paper.quality_score = calculate_quality_score(

            paper

        )


        results.append(

            paper

        )



    return results