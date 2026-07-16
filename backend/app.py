from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware

from fastapi.responses import HTMLResponse


from services.search.search_service import search_papers

from services.email.daily_email import build_daily_email



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

    limit: int = 50,

    cursor: str = "*"

):


    data = search_papers(

        query=q,

        page_size=limit,

        cursor=cursor

    )



    papers = data["papers"]


    next_cursor = data["next_cursor"]


    total_count = data["total_count"]



    result = []



    for paper in papers:


        result.append(

            {


                "score": paper.score,


                "title": paper.title,


                "highlighted_title":

                    paper.highlighted_title,


                "authors":

                    paper.authors,


                "journal":

                    paper.journal,


                "publisher":

                    paper.publisher,


                "year":

                    paper.year,


                "publication_date":

                    paper.publication_date,


                "abstract":

                    paper.abstract,


                "highlighted_abstract":

                    paper.highlighted_abstract,


                "keywords":

                    paper.keywords,


                "subjects":

                    paper.subjects,


                "matched_keywords":

                    paper.matched_keywords,


                "citation":

                    paper.citation,


                "doi":

                    paper.doi,


                "doi_url":

                    paper.doi_url,


                "pdf_url":

                    paper.pdf_url,


                "url":

                    paper.url,


                "language":

                    paper.language,


                "is_open_access":

                    paper.is_open_access,


                "source":

                    paper.source


            }

        )



    return {


        "query": q,


        "count":

            len(result),


        "total":

            total_count,


        # 当前请求使用的cursor

        "cursor":

            cursor,


        # 下一页需要使用的cursor

        "next_cursor":

            next_cursor,


        "results":

            result


    }




# ==========================================================
# Daily Email
# ==========================================================

@app.get(

    "/daily-email",

    response_class=HTMLResponse

)

def daily_email():

    return build_daily_email()



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