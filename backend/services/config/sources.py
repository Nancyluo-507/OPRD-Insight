# ==========================================================
# ChemVigil Source Configuration
# ==========================================================


from services.sources.openalex import search_openalex

from services.sources.crossref import search_crossref

from services.sources.pubmed import search_pubmed

from services.sources.local_db import search_local_db



# ==========================================================
# Source Registry
# ==========================================================

# priority: 数字越大越优先（排名时先排最高优先级的来源）


SEARCH_SOURCES = {


    "openalex": {

        "name": "OpenAlex",

        "enabled": True,

        "priority": 100,

        "handler": search_openalex

    },


    "crossref": {

        "name": "CrossRef",

        "enabled": True,

        "priority": 90,

        "handler": search_crossref

    },


    "pubmed": {

        "name": "PubMed",

        "enabled": True,

        "priority": 80,

        "handler": search_pubmed

    },


    "local_db": {

        "name": "LocalDB",

        "enabled": True,

        "priority": 10,

        "handler": search_local_db

    }


}