from typing import List

from config.settings import settings
from services.models.paper import Paper


def _source_rank(source: str) -> int:
    return settings.SOURCE_PRIORITY.get(source, 0)


# ==========================================================
# Normalize Title
# ==========================================================

def normalize_title(title: str):

    if not title:

        return ""

    title = title.lower()

    chars = [" ", "-", "_", ".", ",", ":", ";", "(", ")", "[", "]"]
    for char in chars:
        title = title.replace(char, "")
    return title


# ==========================================================
# Merge two papers (take best fields from each)
# ==========================================================

def _merge_paper(a: Paper, b: Paper) -> Paper:

    if _source_rank(a.source) >= _source_rank(b.source):
        primary, secondary = a, b
    else:
        primary, secondary = b, a

    merged = Paper(
        title=primary.title or secondary.title,
        source=primary.source,
    )

    merged.authors = primary.authors or secondary.authors
    merged.year = primary.year or secondary.year
    merged.journal = primary.journal or secondary.journal
    merged.publisher = primary.publisher or secondary.publisher
    merged.publication_date = primary.publication_date or secondary.publication_date
    merged.language = primary.language or secondary.language
    merged.is_open_access = primary.is_open_access or secondary.is_open_access
    merged.doi = primary.doi or secondary.doi
    merged.doi_url = primary.doi_url or secondary.doi_url
    merged.url = primary.url or secondary.url
    merged.pdf_url = primary.pdf_url or secondary.pdf_url

    merged.citation = max(primary.citation, secondary.citation)

    # Abstract: take the longer one
    if len(primary.abstract) >= len(secondary.abstract):
        merged.abstract = primary.abstract
    else:
        merged.abstract = secondary.abstract

    # Keywords: merge and deduplicate
    merged.keywords = list(dict.fromkeys(primary.keywords + secondary.keywords))

    # Subjects: merge and deduplicate
    merged.subjects = list(dict.fromkeys(primary.subjects + secondary.subjects))

    return merged


# ==========================================================
# Deduplicate with Merging
# ==========================================================

def deduplicate_papers(papers: List[Paper]):

    doi_map = {}
    title_map = {}

    for paper in papers:
        key = None
        if paper.doi:
            key = ("doi", paper.doi.lower().strip())
        else:
            norm_title = normalize_title(paper.title)
            if norm_title:
                key = ("title", norm_title)

        if key is None:
            continue

        if key in doi_map:
            doi_map[key] = _merge_paper(doi_map[key], paper)
        else:
            doi_map[key] = paper

    result = list(doi_map.values())
    result.sort(key=lambda p: _source_rank(p.source), reverse=True)
    return result