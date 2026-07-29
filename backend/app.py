import os
import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Must be first: load .env before any imports
from config.settings import settings
from utils.logger import log
from utils.exceptions import register_exception_handlers
from database.database import init_db

app = FastAPI(title="ChemVigil Literature Platform", version="1.0.0")

# --- Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    dur = int((time.perf_counter() - t0) * 1000)
    if request.url.path.startswith("/api/"):
        log.info(f"{request.method} {request.url.path} {response.status_code} {dur}ms")
    return response


# --- Exception handlers ---
register_exception_handlers(app)

# --- Routers ---
from routers.home import router as home_router
from routers.auth import router as auth_router
from routers.search import router as search_router
from routers.user import router as user_router
from routers.admin import router as admin_router
from routers.cron import router as cron_router

app.include_router(home_router)
app.include_router(auth_router)
app.include_router(search_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(cron_router)

# --- Startup / Shutdown ---

@app.on_event("startup")
def startup():
    init_db()

    # Preload embedding model so first search isn't slow
    from services.core.embedding_match import _get_transformer
    _get_transformer()
    log.info("Embedding model loaded")

    from services.core.job_worker import worker as job_worker
    job_worker.start()
    from services.email.scheduler import start_scheduler
    start_scheduler()
    log.info("Database initialized, job worker & scheduler started")


@app.on_event("shutdown")
def shutdown():
    from services.core.job_worker import worker as job_worker
    job_worker.stop()
    from services.email.scheduler import stop_scheduler
    stop_scheduler()


# --- Frontend Static Files (no-cache) ---

_frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "frontend")

if os.path.isdir(_frontend_dir):

    class NoCacheStaticFiles(StaticFiles):
        def file_response(self, *args, **kwargs):
            resp = super().file_response(*args, **kwargs)
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
            return resp

    app.mount("/app", NoCacheStaticFiles(directory=_frontend_dir, html=True), name="frontend")
    log.info("Frontend mounted at /app (no-cache)")


# --- Run ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
