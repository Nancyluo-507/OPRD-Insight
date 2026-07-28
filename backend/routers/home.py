import time as _time
from fastapi import APIRouter
from database.session import SessionLocal
from database.database import init_db as _init_db
from config.settings import settings

router = APIRouter(prefix="/api/v1")

_start_time = _time.time()


@router.get("/")
def home():
    return {"message": "AI Literature Search Engine", "status": "running"}


@router.get("/health")
def health():
    db_ok = True
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception:
        db_ok = False
    return {
        "status": "ok" if db_ok else "degraded",
        "uptime_sec": int(_time.time() - _start_time),
        "database": "connected" if db_ok else "error",
    }
