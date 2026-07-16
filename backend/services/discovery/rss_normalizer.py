import re

from bs4 import BeautifulSoup

from services.models.rss_paper import RSSPaper


# ==========================================================
# HTML Cleaner
# ==========================================================

def clean_html(text: str) -> str:

    if not text:
        return ""

    return BeautifulSoup(
        text,
        "html.parser"
    ).get_text(
        separator=" ",
        strip=True
    )


# ==========================================================
# Remove Extra Spaces
# ==========================================================

def clean_spaces(text: str) -> str:

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


# ==========================================================
# Extract DOI
# ==========================================================

def extract_doi(text: str) -> str:

    if not text:
        return ""

    match = re.search(

        r"(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)",

        text

    )

    if match:

        return match.group(1)

    return ""


# ==========================================================
# Remove DOI Text
# ==========================================================

def remove_doi(text: str) -> str:

    if not text:
        return ""

    text = re.sub(

        r"doi\s*:?\s*10\.\d{4,9}/[-._;()/:A-Za-z0-9]+",

        "",

        text,

        flags=re.IGNORECASE

    )

    return text


# ==========================================================
# Remove RSS Metadata
# ==========================================================

def remove_metadata(text: str) -> str:

    if not text:
        return ""

    # Nature, Published online...
    text = re.sub(

        r".*?Published online:.*?;",

        "",

        text,

        flags=re.IGNORECASE

    )

    return text


# ==========================================================
# Summary Cleaner
# ==========================================================

def clean_summary(summary: str):

    if not summary:

        return "", ""

    doi = extract_doi(summary)

    summary = clean_html(summary)

    summary = remove_doi(summary)

    summary = remove_metadata(summary)

    summary = clean_spaces(summary)

    return summary, doi


# ==========================================================
# Normalize RSS Entry
# ==========================================================

def normalize_entry(

    entry,

    source: str

) -> RSSPaper:

    title = entry.get(

        "title",

        ""

    )

    url = entry.get(

        "link",

        ""

    )

    raw_summary = (

        entry.get(

            "summary",

            ""

        )

        or

        entry.get(

            "description",

            ""

        )

    )

    summary, doi = clean_summary(

        raw_summary

    )

    published = (

        entry.get(

            "published",

            ""

        )

        or

        entry.get(

            "updated",

            ""

        )

    )

    # ======================================================
    # Future Extension
    # ======================================================

    authors = []

    journal = ""

    publisher = ""

    keywords = []

    subjects = []

    abstract = ""

    # ======================================================

    return RSSPaper(

        title=title,

        summary=summary,

        abstract=abstract,

        url=url,

        published=published,

        source=source,

        doi=doi,

        authors=authors,

        journal=journal,

        publisher=publisher,

        keywords=keywords,

        subjects=subjects

    )