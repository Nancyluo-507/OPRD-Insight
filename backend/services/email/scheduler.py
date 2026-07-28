from apscheduler.schedulers.background import BackgroundScheduler
from services.core.job_worker import enqueue_job

scheduler = BackgroundScheduler()


def enqueue_weekly_fetch():
    fetch_job_id = enqueue_job("FETCH_JOURNAL", payload={"limit": 20, "timeout": 120})
    print(f"[Scheduler] Enqueued FETCH_JOURNAL (id={fetch_job_id})")


def enqueue_daily_fetch():
    fetch_job_id = enqueue_job("FETCH_JOURNAL", payload={"limit": 20, "timeout": 120})
    print(f"[Scheduler] Enqueued daily FETCH_JOURNAL (id={fetch_job_id})")


def enqueue_weekly_summaries():
    from database.database import SessionLocal
    from database.models import User
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        for user in users:
            job_id = enqueue_job("WEEKLY_SUMMARY", user_id=user.id, payload={"user_id": user.id, "send_email": True})
            print(f"[Scheduler] Enqueued WEEKLY_SUMMARY for user {user.id} (job={job_id})")
    finally:
        db.close()


def start_scheduler():
    if scheduler.running:
        return

    scheduler.add_job(
        enqueue_daily_fetch,
        trigger="cron",
        hour=8,
        minute=0,
        id="daily_fetch",
        replace_existing=True,
    )

    scheduler.add_job(
        enqueue_weekly_summaries,
        trigger="cron",
        day_of_week="mon",
        hour=10,
        minute=0,
        id="weekly_summary",
        replace_existing=True,
    )

    scheduler.add_job(
        lambda: enqueue_job("SEND_EMAIL", payload={"kind": "daily"}),
        trigger="cron",
        day_of_week="mon",
        hour=11,
        minute=0,
        id="weekly_email",
        replace_existing=True,
    )

    scheduler.start()
    print("[Scheduler] Daily FETCH at 08:00, Weekly Mon 10:00 SUMMARY (with email), 11:00 EMAIL")


def stop_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=False)
