from dataclasses import dataclass, field
from typing import List


@dataclass
class RSSPaper:

    # ======================================================
    # Basic Information
    # ======================================================

    title: str = ""

    summary: str = ""

    abstract: str = ""

    url: str = ""

    published: str = ""

    source: str = ""

    doi: str = ""

    # ======================================================
    # Optional Metadata
    # ======================================================

    authors: List[str] = field(default_factory=list)

    journal: str = ""

    publisher: str = ""

    keywords: List[str] = field(default_factory=list)

    subjects: List[str] = field(default_factory=list)