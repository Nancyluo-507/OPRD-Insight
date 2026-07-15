from dataclasses import dataclass, field

from typing import List


@dataclass
class Paper:

    # ==========================================
    # Basic
    # ==========================================

    title: str = ""

    authors: str = ""

    abstract: str = ""

    # ==========================================
    # Publication
    # ==========================================

    journal: str = ""

    publisher: str = ""

    publication_date: str = ""

    year: int = 0

    # ==========================================
    # DOI
    # ==========================================

    doi: str = ""

    doi_url: str = ""

    # ==========================================
    # URL
    # ==========================================

    url: str = ""

    pdf_url: str = ""

    # ==========================================
    # Metrics
    # ==========================================

    citation: int = 0

    is_open_access: bool = False

    # ==========================================
    # Classification
    # ==========================================

    keywords: List[str] = field(

        default_factory=list

    )

    subjects: List[str] = field(

        default_factory=list

    )

    language: str = ""

    # ==========================================
    # Recommendation
    # ==========================================

    score: float = 0

    matched_keywords: List[str] = field(

        default_factory=list

    )

    highlighted_title: str = ""

    highlighted_abstract: str = ""

    # ==========================================
    # Source
    # ==========================================

    source: str = ""
from dataclasses import asdict


def paper_to_dict(

    paper: Paper

):

    return asdict(

        paper

    )


if __name__ == "__main__":

    paper = Paper(

        title="Nickel Catalyst",

        year=2025,

        source="OpenAlex"

    )

    print(

        paper

    )

    print()

    print(

        paper_to_dict(

            paper

        )

    )