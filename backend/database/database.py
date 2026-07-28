from sqlalchemy import text
from sqlalchemy import inspect
from database.session import engine, _is_sqlite, SessionLocal, Base  # re-export for backward compat


def init_db():
    """Create all tables and run migrations using SQLAlchemy"""
    from database.models import Base as ModelsBase
    ModelsBase.metadata.create_all(bind=engine)

    # Migration: add missing columns
    conn = engine.connect()
    try:
        inspector = inspect(engine)
        _add_columns(conn, inspector, "papers", {
            "publication_date": "VARCHAR(50)",
            "url": "TEXT",
            "journal": "VARCHAR(255)",
            "publisher": "VARCHAR(255)",
            "source": "VARCHAR(100)",
            "doi_url": "VARCHAR(500)",
        })
        _add_columns(conn, inspector, "users", {
            "password_hash": "VARCHAR(255)",
            "email_verified": "BOOLEAN DEFAULT FALSE",
            "email_verify_token": "VARCHAR(255)",
        })
        _add_columns(conn, inspector, "email_deliveries", {
            "sent_at": "TIMESTAMP",
            "error_message": "TEXT",
        })
        _add_columns(conn, inspector, "topic_article_matches", {
            "interest_id": "INTEGER",
            "semantic_score": "FLOAT",
        })
        conn.commit()

        # Deduplicate + create unique index
        if _is_sqlite:
            conn.execute(text("""
                DELETE FROM topic_article_matches WHERE id NOT IN (
                    SELECT MIN(id) FROM topic_article_matches GROUP BY interest_id, article_doi
                )
            """))
            conn.execute(text(
                "CREATE UNIQUE INDEX IF NOT EXISTS uq_topic_article_matches "
                "ON topic_article_matches(interest_id, article_doi)"
            ))
            # Migration: add missing indexes
        _add_indexes(conn, [
            ("papers", "doi"),
            ("user_journal_follows", "user_id"),
            ("topic_subscriptions", "user_id"),
            ("user_interests", "user_id"),
            ("topic_article_matches", "user_id"),
            ("jobs", "type"),
            ("jobs", "status"),
            ("email_deliveries", "user_id"),
            ("email_deliveries", "status"),
        ])
        conn.commit()
    finally:
        conn.close()


def _add_indexes(conn, indexes):
    """Create indexes if they don't exist (SQLite-safe)."""
    for table, column in indexes:
        name = f"idx_{table}_{column}"
        conn.execute(text(f"CREATE INDEX IF NOT EXISTS {name} ON {table}({column})"))
        print(f"[DB Migration] Index {name}")


def _add_columns(conn, inspector, table, columns):
    existing = {c["name"] for c in inspector.get_columns(table)}
    for col_name, col_type in columns.items():
        if col_name not in existing:
            if _is_sqlite:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
            else:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
            print(f"[DB Migration] Added {table}.{col_name}")
