import xml.etree.ElementTree as ET


from services.models.paper import Paper



# ==========================================================
# Helpers
# ==========================================================


def get_text(element):

    if element is None:

        return ""

    return element.text or ""



# ==========================================================
# DOI Parser
# ==========================================================


def parse_doi(article):


    for item in article.findall(

        ".//ArticleId"

    ):


        if item.attrib.get(

            "IdType"

        ) == "doi":


            doi = item.text or ""


            return (

                doi,

                f"https://doi.org/{doi}"

                if doi

                else ""

            )


    return (

        "",

        ""

    )



# ==========================================================
# Authors
# ==========================================================


def parse_authors(article):


    authors = []


    for author in article.findall(

        ".//Author"

    ):


        last = get_text(

            author.find(

                "LastName"

            )

        )


        fore = get_text(

            author.find(

                "ForeName"

            )

        )


        name = (

            fore +

            " " +

            last

        ).strip()



        if name:

            authors.append(

                name

            )



    return ", ".join(

        authors

    )



# ==========================================================
# Abstract
# ==========================================================


def parse_abstract(article):


    sections = []


    for item in article.findall(

        ".//AbstractText"

    ):


        text = item.text


        if text:

            sections.append(

                text

            )



    return " ".join(

        sections

    )



# ==========================================================
# Journal
# ==========================================================


def parse_journal(article):


    journal = article.find(

        ".//Journal/Title"

    )


    return get_text(

        journal

    )



# ==========================================================
# Year
# ==========================================================


def parse_year(article):


    year = article.find(

        ".//PubDate/Year"

    )


    try:

        return int(

            get_text(year)

        )

    except:

        return 0



# ==========================================================
# Publication Date
# ==========================================================

_MONTH_MAP = {
    "jan":1,"feb":2,"mar":3,"apr":4,"may":5,"jun":6,
    "jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12,
}

def parse_pub_date(article):

    parts = []

    for tag in ("Year", "Month", "Day"):

        el = article.find(f".//PubDate/{tag}")

        if el is not None and el.text:

            val = el.text.strip()

            if tag == "Month":
                val = str(_MONTH_MAP.get(val.lower(), val))

            parts.append(val)

    if not parts:

        return ""

    return "-".join(parts)


# ==========================================================
# Normalize PubMed Article
# ==========================================================


def normalize_pubmed_article(article):


    title = get_text(

        article.find(

            ".//ArticleTitle"

        )

    )


    doi, doi_url = parse_doi(

        article

    )


    paper = Paper(


        title=title,


        authors=parse_authors(

            article

        ),


        abstract=parse_abstract(

            article

        ),


        journal=parse_journal(

            article

        ),


        publisher="PubMed",


        publication_date=parse_pub_date(article),


        year=parse_year(

            article

        ),


        doi=doi,


        doi_url=doi_url,


        url="",


        pdf_url="",


        citation=0,


        is_open_access=False,


        keywords=[],


        subjects=[],


        source="PubMed"

    )


    return paper



# ==========================================================
# Main Parser
# ==========================================================


def parse_pubmed_xml(xml_text):


    papers = []


    if not xml_text:

        return papers



    try:

        root = ET.fromstring(

            xml_text

        )

    except Exception as e:


        print(

            "PubMed XML Parse Error:",

            e

        )


        return papers



    articles = root.findall(

        ".//PubmedArticle"

    )



    for article in articles:


        try:


            paper = normalize_pubmed_article(

                article

            )


            papers.append(

                paper

            )


        except Exception as e:


            print(

                "PubMed Parser Error:",

                repr(e)

            )


            continue



    return papers