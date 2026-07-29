from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, UniqueConstraint
from database.session import Base
from datetime import datetime


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text)
    abstract = Column(Text)
    authors = Column(Text)
    year = Column(Integer)
    publication_date = Column(String, default="")
    doi = Column(String, index=True)
    url = Column(Text, default="")
    journal = Column(String, default="")
    publisher = Column(String, default="")
    subjects = Column(Text)
    keywords = Column(Text)
    source = Column(String, default="")
    cited_by_count = Column(Integer, default=0)
    doi_url = Column(Text, default="")


class Journal(Base):
    __tablename__ = "journals"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    short_name = Column(String)
    publisher = Column(String)
    rss_url = Column(String)
    rss_type = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    password_hash = Column(String, default="")
    is_active = Column(Boolean, default=True)
    email_enabled = Column(Boolean, default=False)
    target_email = Column(String)
    email_verified = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class UserJournalFollow(Base):
    __tablename__ = "user_journal_follows"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    journal_id = Column(Integer, ForeignKey("journals.id"))
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("user_id", "journal_id"),)


class TopicSubscription(Base):
    __tablename__ = "topic_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    keywords = Column(Text)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class UserInterest(Base):
    """用户兴趣画像 - 替代 TopicSubscription"""
    __tablename__ = "user_interests"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    name = Column(String, nullable=False)
    domain = Column(String, default="综合")
    description = Column(Text, default="")
    keywords = Column(Text, default="")
    llm_expanded = Column(Text, nullable=True)
    vector = Column(Text, nullable=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)


class PaperEmbedding(Base):
    """论文向量缓存"""
    __tablename__ = "paper_embeddings"

    id = Column(Integer, primary_key=True)
    paper_doi = Column(String, unique=True)
    domain = Column(String, default="综合")
    vector = Column(Text)
    model_name = Column(String, default="bge-m3")
    updated_at = Column(DateTime, default=datetime.now)


class TopicArticleMatch(Base):
    __tablename__ = "topic_article_matches"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    topic_id = Column(Integer, ForeignKey("topic_subscriptions.id"), nullable=True)
    interest_id = Column(Integer, ForeignKey("user_interests.id"), nullable=True)
    article_doi = Column(String)
    article_title = Column(Text)
    matched_keywords = Column(Text)
    score = Column(Float, default=0)
    semantic_score = Column(Float, default=0)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("interest_id", "article_doi", name="uq_interest_article"),)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True)
    type = Column(String, nullable=False, index=True)
    status = Column(String, default="PENDING", index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    payload = Column(Text, default="{}")
    progress = Column(Text, default="{}")
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    run_after = Column(DateTime, default=datetime.now)
    locked_at = Column(DateTime, nullable=True)
    lock_owner = Column(String, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now)


class JournalFetchState(Base):
    __tablename__ = "journal_fetch_states"

    id = Column(Integer, primary_key=True)
    journal_id = Column(Integer, ForeignKey("journals.id"), unique=True)
    last_fetched_at = Column(DateTime, nullable=True)
    last_successful_from_date = Column(DateTime, nullable=True)
    last_error = Column(String, nullable=True)
    last_item_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class UserArticle(Base):
    __tablename__ = "user_articles"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    doi = Column(String)
    article_title = Column(Text)
    content = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)

    __table_args__ = (UniqueConstraint("user_id", "doi"),)


class TopicFeedback(Base):
    """反馈：记录用户对推荐文献的互动行为，用于优化匹配"""
    __tablename__ = "topic_feedback"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    match_id = Column(Integer, ForeignKey("topic_article_matches.id"), nullable=True)
    article_doi = Column(String)
    action = Column(String)  # "favorited" | "read" | "clicked" | "ignored" | "hidden"
    created_at = Column(DateTime, default=datetime.now)


class WeeklyReport(Base):
    __tablename__ = "weekly_reports"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    run_id = Column(String)
    title = Column(String)
    content_md = Column(Text)
    total_matches = Column(Integer, default=0)
    topic_count = Column(Integer, default=0)
    period_start = Column(DateTime)
    period_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)


class EmailDelivery(Base):
    """邮件投递记录追踪"""
    __tablename__ = "email_deliveries"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    kind = Column(String)  # "new_articles" | "weekly_summary" | "test"
    status = Column(String, default="PENDING", index=True)  # "PENDING" | "SENT" | "FAILED" | "SKIPPED"
    to_email = Column(String)
    subject = Column(String)
    article_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    job_id = Column(Integer, ForeignKey("jobs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    sent_at = Column(DateTime, nullable=True)
