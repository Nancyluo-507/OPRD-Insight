import json
import os
import re

from services.models.paper import Paper
from database.database import SessionLocal
from database.models import Paper as PaperORM


def _search_orm(query: str, limit: int = 50):
    """Search papers using SQLAlchemy ORM (database-agnostic)"""
    words = re.sub(r"[^a-z0-9\s]", "", query.lower()).strip().split()
    if not words:
        return []
    db = SessionLocal()
    try:
        from sqlalchemy import or_
        q = db.query(PaperORM)
        filters = []
        for w in words:
            pat = f"%{w}%"
            filters.append(PaperORM.title.ilike(pat))
            filters.append(PaperORM.abstract.ilike(pat))
        q = q.filter(or_(*filters))
        rows = q.limit(limit).all()
        return rows
    except Exception as e:
        print("Local DB search error:", e)
        return []
    finally:
        db.close()


def _search_json(query: str, limit: int = 50):
    json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "database", "papers.json")
    if not os.path.exists(json_path):
        return []
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            records = json.load(f)
    except:
        return []
    words = re.sub(r"[^a-z0-9\s]", "", query.lower()).strip().split()
    results = []
    for r in records:
        title = (r.get("title") or "").lower()
        abstract = (r.get("abstract") or "").lower()
        if all(w in title or w in abstract for w in words):
            results.append(r)
            if len(results) >= limit:
                break
    return results


def search_local_db(query: str, cursor="*", per_page: int = 50):
    papers = []

    for row in _search_orm(query, per_page):
        subjects = [s.strip() for s in row.subjects.split(";") if s.strip()] if row.subjects else []
        keywords = [s.strip() for s in row.keywords.split(";") if s.strip()] if row.keywords else []
        paper = Paper(
            title=row.title or "",
            abstract=row.abstract or "",
            authors=row.authors or "",
            year=row.year or 0,
            doi=row.doi or "",
            doi_url=row.doi_url or (f"https://doi.org/{row.doi}" if row.doi else ""),
            citation=row.cited_by_count or 0,
            subjects=subjects,
            keywords=keywords,
            publication_date=row.publication_date or str(row.year) if row.year else "",
            source=row.source or "LocalDB",
        )
        papers.append(paper)

    for record in _search_json(query, per_page):
        authors_list = record.get("authors") or []
        if isinstance(authors_list, list):
            authors_str = ", ".join(authors_list)
        else:
            authors_str = str(authors_list)
        yr = record.get("year") or 0
        paper = Paper(
            title=record.get("title") or "",
            abstract=record.get("abstract") or "",
            authors=authors_str,
            year=yr,
            publication_date=str(yr) if yr else "",
            source="LocalDB",
        )
        papers.append(paper)

    return papers, None, len(papers)
