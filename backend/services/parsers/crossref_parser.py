from services.models.paper import Paper


# ==========================================================
# Title
# ==========================================================

def parse_title(item):

    title = item.get(

        "title",

        []

    )


    if isinstance(title, list) and title:

        return title[0]


    return ""



# ==========================================================
# Authors
# ==========================================================

def parse_authors(item):

    authors = item.get(

        "author",

        []

    )


    if not authors:

        return ""


    names = []


    for author in authors:


        given = author.get(

            "given",

            ""

        )


        family = author.get(

            "family",

            ""

        )


        name = (

            given +

            " " +

            family

        ).strip()


        if name:

            names.append(

                name

            )


    return ", ".join(

        names

    )



# ==========================================================
# DOI
# ==========================================================

def parse_doi(item):

    doi = item.get(

        "DOI",

        ""

    )


    if not doi:

        return "", ""


    return (

        doi,

        f"https://doi.org/{doi}"

    )



# ==========================================================
# Journal
# ==========================================================

def parse_journal(item):

    container = item.get(

        "container-title",

        []

    )


    if isinstance(container, list) and container:

        return container[0]


    return ""



# ==========================================================
# Publisher
# ==========================================================

def parse_publisher(item):

    return item.get(

        "publisher",

        ""

    )



# ==========================================================
# Year
# ==========================================================

def parse_year(item):

    date = item.get(

        "published-print",

        item.get(

            "published-online",

            {}

        )

    )


    parts = date.get(

        "date-parts",

        []

    )


    if (

        parts

        and len(parts[0]) > 0

    ):

        return parts[0][0]


    return 0



# ==========================================================
# Publication Date
# ==========================================================

def parse_publication_date(item):

    date = item.get(

        "published-print",

        item.get("published-online", {})

    )

    parts = date.get("date-parts", [])

    if parts and len(parts[0]) > 0:

        return "-".join(f"{x:02d}" if i > 0 else str(x) for i, x in enumerate(parts[0]))


    return ""



# ==========================================================
# Abstract
# ==========================================================

def parse_abstract(item):

    abstract = item.get(

        "abstract",

        ""

    )


    if not abstract:

        return ""


    return abstract



# ==========================================================
# URL
# ==========================================================

def parse_url(item):

    return item.get(

        "URL",

        ""

    )



# ==========================================================
# PDF
# ==========================================================

def parse_pdf(item):

    links = item.get(

        "link",

        []

    )


    for link in links:


        content_type = link.get(

            "content-type",

            ""

        )


        if "pdf" in content_type.lower():

            return link.get(

                "URL",

                ""

            )


    return ""



# ==========================================================
# Citation
# ==========================================================

def parse_citation(item):

    return item.get(

        "is-referenced-by-count",

        0

    )



# ==========================================================
# Normalize CrossRef Paper
# ==========================================================

def normalize_crossref_paper(item):


    doi, doi_url = parse_doi(

        item

    )


    paper = Paper(

        title=parse_title(

            item

        ),


        authors=parse_authors(

            item

        ),


        abstract=parse_abstract(

            item

        ),


        journal=parse_journal(

            item

        ),


        publisher=parse_publisher(

            item

        ),


        publication_date=parse_publication_date(

            item

        ),


        year=parse_year(

            item

        ),


        doi=doi,


        doi_url=doi_url,


        url=parse_url(

            item

        ),


        pdf_url=parse_pdf(

            item

        ),


        citation=parse_citation(

            item

        ),


        is_open_access=False,


        keywords=[],


        subjects=[],


        source="CrossRef"

    )


    return paper