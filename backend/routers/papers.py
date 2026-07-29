from typing import List
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from database.database import SessionLocal
from database.models import Paper
from utils.helpers import require_auth

router = APIRouter(prefix="/api/v1/papers", tags=["papers"])


class PaperUpload(BaseModel):
    title: str
    doi: str = ""
    summary: str = ""
    abstract: str = ""
    url: str = ""
    published: str = ""
    authors: str = ""
    journal: str = ""
    publisher: str = ""
    source: str = ""


class UploadRequest(BaseModel):
    papers: List[PaperUpload]


@router.post("/upload")
def upload_papers(req: UploadRequest, user_id: int = Depends(require_auth)):
    db = SessionLocal()
    try:
        added = 0
        skipped = 0
        for p in req.papers:
            if not p.title.strip():
                continue
            if p.doi:
                exists = db.query(Paper).filter(Paper.doi == p.doi).first()
                if exists:
                    skipped += 1
                    continue
            authors_list = [a.strip() for a in p.authors.split(";") if a.strip()] if p.authors else []
            db.add(Paper(
                title=p.title,
                doi=p.doi,
                abstract=p.summary or p.abstract,
                url=p.url,
                published=p.published,
                authors="; ".join(authors_list),
                journal=p.journal,
                publisher=p.publisher,
                source=p.source or "manual",
            ))
            added += 1
        db.commit()
        return {"added": added, "skipped": skipped}
    finally:
        db.close()
