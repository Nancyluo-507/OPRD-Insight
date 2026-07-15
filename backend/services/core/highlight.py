import re

from services.core.semantic_match import expand_query


# ==========================================================
# Highlight Text
# ==========================================================

def highlight_text(

    text: str,

    query: str

) -> str:

    if not text:

        return ""

    keywords = expand_query(

        query

    )

    # 长词优先，避免 "CO2" 先替换导致
    # "CO2 reduction" 无法完整高亮
    keywords.sort(

        key=len,

        reverse=True

    )

    result = text

    for keyword in keywords:

        pattern = re.compile(

            re.escape(keyword),

            re.IGNORECASE

        )

        result = pattern.sub(

            lambda m:
            f"<mark>{m.group(0)}</mark>",

            result

        )

    return result
# ==========================================================
# Highlight Paper
# ==========================================================

def highlight_paper(

    paper,

    query

):

    paper.highlighted_title = highlight_text(

        paper.title,

        query

    )

    paper.highlighted_abstract = highlight_text(

        paper.abstract,

        query

    )

    return paper
if __name__ == "__main__":

    from services.models.paper import Paper

    paper = Paper(

        title="Nickel single atom catalyst derived from metal organic framework",

        abstract="This catalyst shows excellent CO2 reduction performance."

    )

    paper = highlight_paper(

        paper,

        "nickel MOF CO2"

    )

    print()

    print(

        paper.highlighted_title

    )

    print()

    print(

        paper.highlighted_abstract

    )