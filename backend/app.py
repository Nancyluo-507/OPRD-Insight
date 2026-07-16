from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from services.sources.openalex import search_openalex


# ==========================================================
# FastAPI
# ==========================================================

app = FastAPI(

    title="AI Literature Search Engine",

    version="1.0.0"

)


# ==========================================================
# CORS
# ==========================================================

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "*"

    ],

    allow_credentials=True,

    allow_methods=[

        "*"

    ],

    allow_headers=[

        "*"

    ]

)


# ==========================================================
# Home
# ==========================================================

@app.get("/")

def home():

    return {

        "message":

        "AI Literature Search Engine",

        "status":

        "running"

    }


# ==========================================================
# Health Check
# ==========================================================

@app.get("/health")

def health():

    return {

        "status":

        "ok"

    }


# ==========================================================
# Search
# ==========================================================

@app.get("/search")

def search(

    q: str,

    limit: int = 20

):

    papers, next_cursor, total_count = search_openalex(

        q,

        cursor="*",

        per_page=limit

    )

    result = []
    for paper in papers:

        result.append(

            {

                "score": paper.score,

                "title": paper.title,

                "highlighted_title": paper.highlighted_title,

                "authors": paper.authors,

                "journal": paper.journal,

                "publisher": paper.publisher,

                "year": paper.year,

                "publication_date": paper.publication_date,

                "abstract": paper.abstract,

                "highlighted_abstract": paper.highlighted_abstract,

                "keywords": paper.keywords,

                "subjects": paper.subjects,

                "matched_keywords": paper.matched_keywords,

                "citation": paper.citation,

                "doi": paper.doi,

                "doi_url": paper.doi_url,

                "pdf_url": paper.pdf_url,

                "url": paper.url,

                "language": paper.language,

                "is_open_access": paper.is_open_access,

                "source": paper.source

            }

        )

    return {

        "query": q,

        "count": len(result),

        "total": total_count,

        "next_cursor": next_cursor,

        "results": result

    }


# ==========================================================
# Run
# ==========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(

        "app:app",

        host="127.0.0.1",

        port=8000,

        reload=True

    )
from fastapi.responses import HTMLResponse

from services.email.daily_email import build_daily_email
# ==========================================================
# Daily Email
# ==========================================================

@app.get(

    "/daily-email",

    response_class=HTMLResponse

)

def daily_email():

    return build_daily_email()