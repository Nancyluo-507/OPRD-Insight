from fastapi import APIRouter, Header, HTTPException
from config.settings import settings
from services.core.job_worker import enqueue_job

router = APIRouter(prefix="/api/v1/cron", tags=["cron"])


def _verify(authorization: str = Header(None)):
    secret = settings.get("CRON_SECRET")
    if not secret:
        raise HTTPException(500, "CRON_SECRET not configured on server")
    if authorization != f"Bearer {secret}":
        raise HTTPException(403, "Invalid cron secret")


@router.post("/fetch-journals")
def cron_fetch_journals(authorization: str = Header(None)):
    _verify(authorization)
    job_id = enqueue_job("FETCH_JOURNAL", payload={"limit": 20, "timeout": 120})
    return {"ok": True, "job_id": job_id}


@router.post("/weekly-summaries")
def cron_weekly_summaries(authorization: str = Header(None)):
    _verify(authorization)
    from database.database import SessionLocal
    from database.models import User
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            enqueue_job("WEEKLY_SUMMARY", user_id=user.id, payload={"user_id": user.id, "send_email": True})
        return {"ok": True, "user_count": len(users)}
    finally:
        db.close()
