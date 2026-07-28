from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from database.session import SessionLocal
from database.models import User
from database.crud import list_jobs, list_email_deliveries, delivery_stats
from utils.logger import log
from utils.helpers import require_auth

router = APIRouter(prefix="/api/v1", tags=["admin"])


# ---- Jobs ----

@router.get("/jobs")
def list_jobs_route(limit: int = 20, current_user: int = Depends(require_auth)):
    return {"jobs": list_jobs(limit)}


class EnqueueJobBody(BaseModel):
    type: str
    user_id: int = None
    payload: dict = {}


@router.post("/jobs/enqueue")
def enqueue_job(body: EnqueueJobBody, current_user: int = Depends(require_auth)):
    from services.core.job_worker import enqueue_job as enq
    job_id = enq(body.type, user_id=body.user_id, payload=body.payload)
    return {"job_id": job_id}


# ---- Email Deliveries ----

@router.get("/email-deliveries")
def list_email_deliveries_route(limit: int = 50, current_user: int = Depends(require_auth)):
    return {"deliveries": list_email_deliveries(limit)}


@router.post("/email-deliveries/retry")
def retry_failed_deliveries(current_user: int = Depends(require_auth)):
    from services.core.job_worker import enqueue_job as enq
    job_id = enq("RETRY_EMAILS", payload={})
    return {"job_id": job_id, "message": "Retry job enqueued"}


@router.get("/email-deliveries/stats")
def delivery_stats_route(current_user: int = Depends(require_auth)):
    return delivery_stats()


# ---- Trigger Endpoints ----

@router.post("/trigger-fetch")
def trigger_fetch(current_user: int = Depends(require_auth)):
    from services.core.job_worker import enqueue_job as enq
    job_id = enq("FETCH_JOURNAL", payload={"limit": 20, "timeout": 120})
    return HTMLResponse(f'<script>alert("Fetch job enqueued: #{job_id}"); window.location.href="/daily-email";</script>')


@router.post("/trigger-summary")
def trigger_summary(current_user: int = Depends(require_auth)):
    from services.core.job_worker import enqueue_job as enq
    db2 = SessionLocal()
    try:
        users = db2.query(User).filter(User.is_active == True).all()
        for u in users:
            enq("WEEKLY_SUMMARY", user_id=u.id, payload={"user_id": u.id, "send_email": True})
    finally:
        db2.close()
    return HTMLResponse(f'<script>alert("Summary enqueued for {len(users)} users"); window.location.href="/daily-email";</script>')


@router.post("/trigger-push-new")
def trigger_push_new(current_user: int = Depends(require_auth)):
    from services.core.job_worker import enqueue_job as enq
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True, User.email_enabled == True).all()
        for u in users:
            enq("NEW_ARTICLES", user_id=u.id, payload={"user_id": u.id})
    finally:
        db.close()
    return HTMLResponse(f'<script>alert("Push enqueued for {len(users)} users"); window.location.href="/daily-email";</script>')
