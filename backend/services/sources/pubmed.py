import requests


from services.core.query_processor import process_query



# ==========================================================
# Config
# ==========================================================

PUBMED_SEARCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils/esearch.fcgi"
)


PUBMED_FETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/"
    "entrez/eutils/efetch.fcgi"
)


DEFAULT_PER_PAGE = 50

TIMEOUT = 30



session = requests.Session()


session.headers.update(

    {

        "User-Agent":

        "ChemVigil/1.0"

    }

)



# ==========================================================
# Request IDs
# ==========================================================

def request_pubmed_ids(

    query: str,

    retmax: int = DEFAULT_PER_PAGE

):


    response = session.get(

        PUBMED_SEARCH_URL,

        params={

            "db":

                "pubmed",

            "term":

                query,

            "retmax":

                retmax,

            "retmode":

                "json",

            "sort":

                "relevance"

        },

        timeout=TIMEOUT

    )


    response.raise_for_status()


    data = response.json()



    result = data.get(

        "esearchresult",

        {}

    )



    ids = result.get(

        "idlist",

        []

    )



    total_count = int(

        result.get(

            "count",

            0

        )

    )



    return (

        ids,

        total_count

    )



# ==========================================================
# Fetch Details
# ==========================================================

def fetch_pubmed_details(

    ids

):


    if not ids:

        return ""



    response = session.get(

        PUBMED_FETCH_URL,

        params={

            "db":

                "pubmed",

            "id":

                ",".join(ids),

            "retmode":

                "xml"

        },

        timeout=TIMEOUT

    )


    response.raise_for_status()


    return response.text



# ==========================================================
# Search PubMed
# ==========================================================

def search_pubmed(

    query: str,

    cursor="*",

    per_page: int = DEFAULT_PER_PAGE

):


    from services.parsers.pubmed_parser import (

        parse_pubmed_xml

    )



    # ======================================================
    # Query Processing
    # ======================================================

    query_info = process_query(

        query

    )


    search_query = query_info.get(

        "search_query",

        query

    )



    print(

        "PubMed Query:",

        search_query

    )



    # ======================================================
    # Search IDs
    # ======================================================

    ids, total_count = request_pubmed_ids(

        search_query,

        retmax=per_page

    )



    print(

        "PubMed IDs:",

        len(ids),

        "Total:",

        total_count

    )



    # ======================================================
    # Fetch XML
    # ======================================================

    xml = fetch_pubmed_details(

        ids

    )


    print(

        "PubMed XML length:",

        len(xml)

    )



    # ======================================================
    # Parse
    # ======================================================

    papers = parse_pubmed_xml(

        xml

    )


    print(

        "PubMed Parsed papers:",

        len(papers)

    )



    return (

        papers,

        None,

        total_count

    )