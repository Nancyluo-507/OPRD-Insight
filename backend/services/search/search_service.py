from services.search.source_manager import search_all_sources


def search_papers(
    query: str,
    page_size: int = 10,
    cursor: str = "*",
    time_range: str = "all",
):
    data = search_all_sources(
        query=query,
        per_source=page_size,
        time_range=time_range,
    )

    return {
        "papers": data["papers"],
        "next_cursor": data["cursors"],
        "total_count": data["total_count"],
    }
