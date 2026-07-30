from database.session import SessionLocal
from database.models import (
    User, Journal, UserJournalFollow, TopicSubscription, UserInterest,
    TopicArticleMatch, UserArticle, WeeklyReport, TopicFeedback, EmailDelivery, Job,
)
from utils.helpers import row_to_dict
from datetime import datetime, timedelta


# ========== User ==========

def get_user(user_id: int) -> dict | None:
    db = SessionLocal()
    try:
        return row_to_dict(db.query(User).filter(User.id == user_id).first())
    finally:
        db.close()

def get_user_by_name(name: str) -> User | None:
    db = SessionLocal()
    try:
        return db.query(User).filter(User.name == name).first()
    finally:
        db.close()

def create_user(name: str, password_hash: str, email: str) -> User:
    db = SessionLocal()
    try:
        user = User(name=name, password_hash=password_hash, target_email=email)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()

def update_user_settings(user_id: int, email_enabled: bool, target_email: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.email_enabled = email_enabled
            user.target_email = target_email
            db.commit()
    finally:
        db.close()

# ========== Journals ==========

def list_journals(search: str = "", publisher: str = "") -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(Journal).order_by(Journal.publisher, Journal.title)
        if search:
            q = q.filter(Journal.title.ilike(f"%{search}%"))
        if publisher:
            q = q.filter(Journal.publisher == publisher)
        return [row_to_dict(j) for j in q.all()]
    finally:
        db.close()


# ========== Follows ==========

def list_follows(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        follows = db.query(UserJournalFollow).filter(UserJournalFollow.user_id == user_id).all()
        ids = [f.journal_id for f in follows]
        if not ids:
            return []
        return [row_to_dict(j) for j in db.query(Journal).filter(Journal.id.in_(ids)).all()]
    finally:
        db.close()

def follow_journal(user_id: int, journal_id: int):
    db = SessionLocal()
    try:
        exists = db.query(UserJournalFollow).filter(
            UserJournalFollow.user_id == user_id, UserJournalFollow.journal_id == journal_id,
        ).first()
        if not exists:
            db.add(UserJournalFollow(user_id=user_id, journal_id=journal_id))
            db.commit()
    finally:
        db.close()

def unfollow_journal(user_id: int, journal_id: int):
    db = SessionLocal()
    try:
        db.query(UserJournalFollow).filter(
            UserJournalFollow.user_id == user_id, UserJournalFollow.journal_id == journal_id,
        ).delete()
        db.commit()
    finally:
        db.close()


# ========== Topics ==========

def list_topics(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(TopicSubscription).filter(TopicSubscription.user_id == user_id).order_by(TopicSubscription.created_at.desc())
        return [row_to_dict(t) for t in q.all()]
    finally:
        db.close()

def create_topic(user_id: int, name: str, keywords: str) -> TopicSubscription:
    db = SessionLocal()
    try:
        topic = TopicSubscription(user_id=user_id, name=name, keywords=keywords)
        db.add(topic)
        db.commit()
        db.refresh(topic)
        return topic
    finally:
        db.close()

def get_topic(topic_id: int) -> TopicSubscription | None:
    db = SessionLocal()
    try:
        return db.query(TopicSubscription).filter(TopicSubscription.id == topic_id).first()
    finally:
        db.close()

def update_topic(topic_id: int, name: str = None, keywords: str = None, enabled: bool = None):
    db = SessionLocal()
    try:
        topic = db.query(TopicSubscription).filter(TopicSubscription.id == topic_id).first()
        if name is not None:
            topic.name = name
        if keywords is not None:
            topic.keywords = keywords
        if enabled is not None:
            topic.enabled = enabled
        db.commit()
        return topic
    finally:
        db.close()

def delete_topic(topic_id: int):
    db = SessionLocal()
    try:
        db.query(TopicArticleMatch).filter(TopicArticleMatch.topic_id == topic_id).delete()
        db.query(TopicFeedback).filter(TopicFeedback.match_id == topic_id).delete()
        db.query(TopicSubscription).filter(TopicSubscription.id == topic_id).delete()
        db.commit()
    finally:
        db.close()


# ========== Interests ==========

def list_interests(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(UserInterest).filter(UserInterest.user_id == user_id).order_by(UserInterest.created_at.desc())
        return [row_to_dict(i) for i in q.all()]
    finally:
        db.close()

def get_interest(interest_id: int) -> UserInterest | None:
    db = SessionLocal()
    try:
        return db.query(UserInterest).filter(UserInterest.id == interest_id).first()
    finally:
        db.close()

def delete_interest(interest_id: int):
    db = SessionLocal()
    try:
        interest = db.query(UserInterest).filter(UserInterest.id == interest_id).first()
        if interest:
            db.delete(interest)
            db.commit()
    finally:
        db.close()


# ========== Matches ==========

def list_matches(user_id: int, topic_id: int = None, days: int = 7) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(TopicArticleMatch).filter(
            TopicArticleMatch.user_id == user_id,
            TopicArticleMatch.created_at >= datetime.now() - timedelta(days=days),
        )
        if topic_id:
            q = q.filter(TopicArticleMatch.topic_id == topic_id)
        return [row_to_dict(m) for m in q.order_by(TopicArticleMatch.created_at.desc()).all()]
    finally:
        db.close()


# ========== User Articles ==========

def save_article(user_id: int, doi: str, title: str, content: str, is_favorite: bool, is_read: bool) -> dict:
    db = SessionLocal()
    try:
        article = db.query(UserArticle).filter(
            UserArticle.user_id == user_id, UserArticle.doi == doi,
        ).first()
        if article:
            article.is_favorite = is_favorite
            article.is_read = is_read
            if title:
                article.article_title = title
            if content:
                article.content = content
        else:
            article = UserArticle(user_id=user_id, doi=doi, article_title=title, content=content, is_favorite=is_favorite, is_read=is_read)
            db.add(article)
        db.commit()
        db.refresh(article)
        return {"is_favorite": article.is_favorite, "is_read": article.is_read}
    finally:
        db.close()

def list_favorites(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(UserArticle).filter(UserArticle.user_id == user_id, UserArticle.is_favorite == True).order_by(UserArticle.created_at.desc())
        return [row_to_dict(a) for a in q.all()]
    finally:
        db.close()

def list_history(user_id: int) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(UserArticle).filter(UserArticle.user_id == user_id, UserArticle.is_read == True).order_by(UserArticle.created_at.desc())
        return [row_to_dict(a) for a in q.all()]
    finally:
        db.close()

def list_user_articles(user_id: int, is_favorite: bool = None, is_read: bool = None) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(UserArticle).filter(UserArticle.user_id == user_id)
        if is_favorite is not None:
            q = q.filter(UserArticle.is_favorite == is_favorite)
        if is_read is not None:
            q = q.filter(UserArticle.is_read == is_read)
        return [row_to_dict(a) for a in q.order_by(UserArticle.created_at.desc()).all()]
    finally:
        db.close()


# ========== Feedback ==========

def add_feedback(user_id: int, article_doi: str, action: str, match_id: int = None):
    db = SessionLocal()
    try:
        db.add(TopicFeedback(user_id=user_id, match_id=match_id, article_doi=article_doi, action=action))
        db.commit()
    finally:
        db.close()

def feedback_stats(user_id: int, days: int = 30) -> dict:
    db = SessionLocal()
    try:
        cutoff = datetime.now() - timedelta(days=days)
        rows = db.query(TopicFeedback).filter(TopicFeedback.user_id == user_id, TopicFeedback.created_at >= cutoff).all()
        engaged = sum(1 for r in rows if r.action in ("favorited", "read", "clicked"))
        ignored = sum(1 for r in rows if r.action in ("ignored", "hidden"))
        return {
            "total": len(rows),
            "engaged": engaged,
            "ignored": ignored,
            "engagement_rate": round(engaged / max(len(rows), 1) * 100, 1),
            "by_action": {a: sum(1 for r in rows if r.action == a) for a in set(r.action for r in rows)},
        }
    finally:
        db.close()


# ========== Reports ==========

def list_reports(user_id: int, limit: int = 10) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(WeeklyReport).filter(WeeklyReport.user_id == user_id).order_by(WeeklyReport.created_at.desc()).limit(limit)
        return [row_to_dict(r) for r in q.all()]
    finally:
        db.close()

def get_report(report_id: int) -> dict | None:
    db = SessionLocal()
    try:
        return row_to_dict(db.query(WeeklyReport).filter(WeeklyReport.id == report_id).first())
    finally:
        db.close()


# ========== Email Deliveries ==========

def list_email_deliveries(limit: int = 50) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(EmailDelivery).order_by(EmailDelivery.created_at.desc()).limit(limit)
        return [row_to_dict(d) for d in q.all()]
    finally:
        db.close()

def list_user_email_deliveries(user_id: int, limit: int = 30) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(EmailDelivery).filter(EmailDelivery.user_id == user_id).order_by(EmailDelivery.created_at.desc()).limit(limit)
        return [row_to_dict(d) for d in q.all()]
    finally:
        db.close()

def delivery_stats() -> dict:
    db = SessionLocal()
    try:
        total = db.query(EmailDelivery).count()
        sent = db.query(EmailDelivery).filter(EmailDelivery.status == "SENT").count()
        failed = db.query(EmailDelivery).filter(EmailDelivery.status == "FAILED").count()
        return {"total": total, "sent": sent, "failed": failed, "success_rate": round(sent / max(total, 1) * 100, 1)}
    finally:
        db.close()


# ========== Jobs ==========

def list_jobs(limit: int = 20) -> list[dict]:
    db = SessionLocal()
    try:
        q = db.query(Job).order_by(Job.created_at.desc()).limit(limit)
        return [row_to_dict(j) for j in q.all()]
    finally:
        db.close()
