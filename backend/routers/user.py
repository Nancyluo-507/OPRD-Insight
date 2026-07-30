from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from utils.helpers import require_auth
from database.session import SessionLocal
from database.models import User, TopicArticleMatch, TopicFeedback, UserInterest
from database.crud import (
    get_user, get_user_by_name, list_journals, list_follows, follow_journal, unfollow_journal,
    list_topics, create_topic, update_topic, delete_topic, get_topic,
    list_interests, get_interest, delete_interest,
    list_matches, save_article, list_favorites, list_history, list_user_articles,
    add_feedback, feedback_stats,
    list_reports, get_report, list_user_email_deliveries,
)
from utils.helpers import row_to_dict
from utils.exceptions import AppException
from utils.logger import log
from datetime import datetime
import json

router = APIRouter(prefix="/api/v1", tags=["user"])


# ---- User ----

@router.post("/user/init")
def init_user(name: str = "default"):
    existing = get_user_by_name(name)
    if existing:
        return existing
    db = SessionLocal()
    try:
        user = User(name=name)
        db.add(user)
        db.commit()
        db.refresh(user)
        return row_to_dict(user)
    finally:
        db.close()


@router.get("/user/{user_id}")
def get_user_route(user_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    user = get_user(user_id)
    if not user:
        raise AppException("User not found", 404)
    return user


class UpdateSettingsBody(BaseModel):
    email_enabled: bool = False
    target_email: str = ""


@router.put("/user/{user_id}/settings")
def update_settings(user_id: int, body: UpdateSettingsBody, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise AppException("User not found", 404)
        user.email_enabled = body.email_enabled
        user.target_email = body.target_email
        db.commit()
        return {"status": "ok"}
    finally:
        db.close()


# ---- Journals ----

@router.get("/journals")
def list_journals_route(search: str = "", publisher: str = ""):
    return {"journals": list_journals(search, publisher)}


@router.get("/user/{user_id}/follows")
def list_follows_route(user_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"journals": list_follows(user_id)}


@router.post("/user/{user_id}/follow/{journal_id}")
def follow_journal_route(user_id: int, journal_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    follow_journal(user_id, journal_id)
    return {"status": "ok"}


@router.delete("/user/{user_id}/follow/{journal_id}")
def unfollow_journal_route(user_id: int, journal_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    unfollow_journal(user_id, journal_id)
    return {"status": "ok"}


# ---- Topics ----

@router.get("/user/{user_id}/topics")
def list_topics_route(user_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"topics": list_topics(user_id)}


class CreateTopicBody(BaseModel):
    name: str
    keywords: str = ""


@router.post("/user/{user_id}/topics")
def create_topic_route(user_id: int, body: CreateTopicBody, current_user: int = Depends(require_auth)):
    topic = create_topic(user_id, body.name, body.keywords)
    try:
        from services.core.job_worker import enqueue_job as enq
        enq("FETCH_JOURNAL", user_id=user_id, payload={"limit": 5, "timeout": 60})
    except Exception:
        pass
    return row_to_dict(topic)


class UpdateTopicBody(BaseModel):
    name: str = None
    keywords: str = None
    enabled: bool = None


@router.put("/topics/{topic_id}")
def update_topic_route(topic_id: int, body: UpdateTopicBody, current_user: int = Depends(require_auth)):
    topic = update_topic(topic_id, name=body.name, keywords=body.keywords, enabled=body.enabled)
    if not topic:
        raise AppException("Topic not found", 404)
    return row_to_dict(topic)


@router.delete("/topics/{topic_id}")
def delete_topic_route(topic_id: int, current_user: int = Depends(require_auth)):
    delete_topic(topic_id)
    return {"status": "ok"}


# ---- Domains ----

@router.get("/domains")
def list_domains():
    from services.domain.domain_keywords import get_domain_list
    return {"domains": get_domain_list()}


# ---- Interests ----

class CreateInterestBody(BaseModel):
    name: str
    domain: str = "综合"
    description: str = ""
    keywords: str = ""


@router.get("/user/{user_id}/interests")
def list_interests_route(user_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"interests": list_interests(user_id)}


@router.post("/user/{user_id}/interests")
def create_interest(user_id: int, body: CreateInterestBody, current_user: int = Depends(require_auth)):
    from services.matching.llm_expander import expand_query
    from services.matching.encoder import encode_user_interest
    db = SessionLocal()
    try:
        interest = UserInterest(
            user_id=user_id, name=body.name, domain=body.domain,
            description=body.description, keywords=body.keywords,
        )
        expanded = expand_query(body.description, body.keywords)
        if expanded and expanded != body.description:
            interest.llm_expanded = expanded
        try:
            vec = encode_user_interest(expanded or body.description, body.keywords)
            if vec:
                interest.vector = json.dumps(vec)
        except Exception as e:
            log.warning(f"[CreateInterest] Encoding deferred: {e}")
        db.add(interest)
        db.commit()
        db.refresh(interest)
        return row_to_dict(interest)
    finally:
        db.close()


@router.put("/interests/{interest_id}")
def update_interest(interest_id: int, body: CreateInterestBody, current_user: int = Depends(require_auth)):
    from services.matching.llm_expander import expand_query
    from services.matching.encoder import encode_user_interest
    db = SessionLocal()
    try:
        interest = db.query(UserInterest).filter(UserInterest.id == interest_id).first()
        if not interest:
            raise AppException("Interest not found", 404)
        interest.name = body.name
        interest.domain = body.domain
        interest.description = body.description
        interest.keywords = body.keywords
        expanded = expand_query(body.description, body.keywords)
        if expanded and expanded != body.description:
            interest.llm_expanded = expanded
        vec = encode_user_interest(expanded or body.description, body.keywords)
        if vec:
            interest.vector = json.dumps(vec)
        db.commit()
        return row_to_dict(interest)
    finally:
        db.close()


@router.delete("/interests/{interest_id}")
def delete_interest_route(interest_id: int, current_user: int = Depends(require_auth)):
    interest = get_interest(interest_id)
    if not interest:
        raise AppException("Interest not found", 404)
    delete_interest(interest_id)
    return {"status": "ok"}


# ---- Matches ----

@router.get("/user/{user_id}/matches")
def list_matches_route(user_id: int, current_user: int = Depends(require_auth), topic_id: int = None, days: int = 7):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"matches": list_matches(user_id, topic_id, days)}


# ---- User Articles ----

class SaveArticleBody(BaseModel):
    doi: str
    article_title: str = ""
    content: str = ""
    is_favorite: bool = False
    is_read: bool = False


@router.post("/user/{user_id}/articles")
def save_user_article(user_id: int, body: SaveArticleBody, current_user: int = Depends(require_auth)):
    result = save_article(user_id, body.doi, body.article_title, body.content, body.is_favorite, body.is_read)
    if body.is_favorite:
        add_feedback(user_id, body.doi, "favorited")
    if body.is_read:
        pass  # feedback handled inside crud
    return {"status": "ok", "is_favorite": result["is_favorite"]}


@router.get("/user/{user_id}/favorites")
def list_favorites_route(user_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"articles": list_favorites(user_id)}


@router.get("/user/{user_id}/history")
def list_history_route(user_id: int, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"articles": list_history(user_id)}


@router.get("/user/{user_id}/articles")
def list_user_articles_route(user_id: int, current_user: int = Depends(require_auth), is_favorite: bool = None, is_read: bool = None):
    return {"articles": list_user_articles(user_id, is_favorite, is_read)}


# ---- Feedback ----

class SubmitFeedbackBody(BaseModel):
    article_doi: str
    match_id: int = None
    action: str


@router.post("/user/{user_id}/feedback")
def submit_feedback(user_id: int, body: SubmitFeedbackBody, current_user: int = Depends(require_auth)):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    add_feedback(user_id, body.article_doi, body.action, body.match_id)
    return {"status": "ok"}


@router.get("/user/{user_id}/feedback/stats")
def feedback_stats_route(user_id: int, current_user: int = Depends(require_auth), days: int = 30):
    return feedback_stats(user_id, days)


# ---- Reports ----

@router.get("/user/{user_id}/reports")
def list_reports_route(user_id: int, current_user: int = Depends(require_auth), limit: int = 10):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"reports": list_reports(user_id, limit)}


@router.get("/reports/{report_id}")
def get_report_route(report_id: int, current_user: int = Depends(require_auth)):
    report = get_report(report_id)
    if not report:
        raise AppException("Report not found", 404)
    return report


# ---- Email Deliveries ----

@router.get("/user/{user_id}/email-deliveries")
def list_user_email_deliveries_route(user_id: int, current_user: int = Depends(require_auth), limit: int = 30):
    if current_user != user_id:
        raise HTTPException(403, "Forbidden")
    return {"deliveries": list_user_email_deliveries(user_id, limit)}
