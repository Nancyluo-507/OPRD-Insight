from services.sources.openalex import search_openalex


# ==========================================================
# Unified Search Service
# ==========================================================

def search_papers(

    query: str,

    page_size: int = 10,

    cursor: str = "*"

):

    # 第一版：先直接调用 OpenAlex

    papers, next_cursor, total_count = search_openalex(

        query,

        cursor=cursor,

        per_page=page_size

    )

    return {

        "papers": papers,

        "next_cursor": next_cursor,

        "total_count": total_count

    }