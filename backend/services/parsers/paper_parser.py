from services.models.paper import Paper


# ==========================================================
# Authors
# ==========================================================

def parse_authors(authorships):

    if not authorships:

        return ""

    authors = []

    for item in authorships:

        author = item.get(

            "author",

            {}

        )

        name = author.get(

            "display_name",

            ""

        )

        if name:

            authors.append(

                name

            )

    return ", ".join(

        authors

    )


# ==========================================================
# DOI
# ==========================================================

def parse_doi(

    doi

):

    if not doi:

        return "", ""

    doi = doi.replace(

        "https://doi.org/",

        ""

    )

    return doi, f"https://doi.org/{doi}"


# ==========================================================
# PDF URL
# ==========================================================

def parse_pdf(

    work

):

    locations = work.get(

        "locations",

        []

    )

    for location in locations:

        pdf = location.get(

            "pdf_url"

        )

        if pdf:

            return pdf

    return ""


# ==========================================================
# Abstract
# ==========================================================

def parse_abstract(

    inverted_index

):

    if not inverted_index:

        return ""

    max_position = -1

    for positions in inverted_index.values():

        if positions:

            max_position = max(

                max_position,

                max(

                    positions

                )

            )

    if max_position == -1:

        return ""

    words = [

        ""

    ] * (

        max_position + 1

    )

    for word, positions in inverted_index.items():

        for position in positions:

            words[position] = word

    return " ".join(

        words

    )


# ==========================================================
# Concepts
# ==========================================================

def parse_concepts(

    concepts

):

    keywords = []

    subjects = []

    if not concepts:

        return keywords, subjects

    for item in concepts:

        name = item.get(

            "display_name",

            ""

        )

        if not name:

            continue

        subjects.append(

            name

        )

        if item.get(

            "score",

            0

        ) >= 0.30:

            keywords.append(

                name

            )


    return keywords, subjects


# ==========================================================
# Normalize OpenAlex Paper
# ==========================================================

def normalize_openalex_paper(

    work

) -> Paper:

    doi, doi_url = parse_doi(

        work.get(

            "doi"

        )

    )

    keywords, subjects = parse_concepts(

        work.get(

            "concepts",

            []

        )

    )

    paper = Paper(

        title=work.get(

            "display_name",

            ""

        ),

        authors=parse_authors(

            work.get(

                "authorships",

                []

            )

        ),

        abstract=parse_abstract(

            work.get(

                "abstract_inverted_index",

                {}

            )

        ),
                journal=work.get(

            "primary_location",

            {}

        ).get(

            "source",

            {}

        ).get(

            "display_name",

            ""

        ),

        publisher=work.get(

            "primary_location",

            {}

        ).get(

            "source",

            {}

        ).get(

            "host_organization_name",

            ""

        ),

        publication_date=work.get(

            "publication_date",

            ""

        ),

        year=work.get(

            "publication_year",

            0

        ),

        doi=doi,

        doi_url=doi_url,

        url=work.get(

            "id",

            ""

        ),

        pdf_url=parse_pdf(

            work

        ),

        citation=work.get(

            "cited_by_count",

            0

        ),

        is_open_access=work.get(

            "open_access",

            {}

        ).get(

            "is_oa",

            False

        ),

        keywords=keywords,

        subjects=subjects,

        source="OpenAlex"

    )

    return paper


if __name__ == "__main__":

    demo = {

        "display_name":

        "Nickel catalyst for CO2 reduction",

        "publication_year": 2025,

        "publication_date": "2025-01-01",

        "doi":

        "https://doi.org/10.1234/test",

        "cited_by_count": 85,

        "id":

        "https://openalex.org/W123456",

        "open_access": {

            "is_oa": True

        },

        "primary_location": {

            "source": {

                "display_name":

                "Nature Catalysis",

                "host_organization_name":

                "Nature"

            }

        },

        "authorships": [

            {

                "author": {

                    "display_name":

                    "Alice"

                }

            },

            {

                "author": {

                    "display_name":

                    "Bob"

                }

            }

        ],

        "abstract_inverted_index": {

            "Nickel": [0],

            "single": [1],

            "atom": [2],

            "catalyst": [3],

            "for": [4],

            "CO2": [5],

            "reduction": [6]

        },

        "concepts": [

            {

                "display_name": "Nickel",

                "score": 0.98

            },

            {

                "display_name": "Metal Organic Framework",

                "score": 0.91

            },

            {

                "display_name": "Electrocatalysis",

                "score": 0.84

            }

        ]

    }

    paper = normalize_openalex_paper(

        demo

    )

    print()

    print("Title:")

    print(

        paper.title

    )

    print()

    print("Authors:")

    print(

        paper.authors

    )

    print()

    print("Abstract:")

    print(

        paper.abstract

    )

    print()

    print("Keywords:")

    print(

        paper.keywords

    )

    print()

    print("Subjects:")

    print(

        paper.subjects

    )

    print()

    print("DOI:")

    print(

        paper.doi

    )

    print()

    print("Source:")

    print(

        paper.source

    )