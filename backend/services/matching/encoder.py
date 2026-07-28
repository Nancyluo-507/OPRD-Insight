import json
import os
import re
import sys
import numpy as np
from database.database import SessionLocal
from database.models import PaperEmbedding

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["HF_HUB_OFFLINE"] = "1"

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def _is_chinese(text: str) -> bool:
    return bool(re.search(r'[\u4e00-\u9fff]', text))

def _to_en(text: str) -> str:
    if not _is_chinese(text):
        return text
    try:
        from services.translate.translator import translate_text
        return translate_text(text, mode="llm") or text
    except Exception as e:
        print(f"[Encoder] Translation failed: {e}")
        return text

def _get_model():
    global _model
    if _model is None:
        old_stderr = sys.stderr
        try:
            sys.stderr = open(os.devnull, 'w')
            os.environ["TQDM_DISABLE"] = "1"
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(MODEL_NAME, local_files_only=True)
        except Exception:
            pass
        finally:
            try:
                sys.stderr.close()
            except Exception:
                pass
            sys.stderr = old_stderr
    return _model

def encode_text(text: str) -> list:
    if not text or not text.strip():
        return None
    model = _get_model()
    if model is None:
        return None
    vec = model.encode(text, normalize_embeddings=True)
    return vec.tolist()

def encode_paper(title="", abstract="", summary="") -> list:
    parts = []
    if title:
        parts += [title, title]
    if abstract:
        parts += [abstract]
    if summary:
        parts += [summary]
    text = ". ".join(parts)
    if not text.strip():
        return None
    return encode_text(text)

def get_or_compute_embedding(paper_doi: str, title="", abstract="", summary="", domain="综合"):
    db = SessionLocal()
    try:
        existing = db.query(PaperEmbedding).filter(PaperEmbedding.paper_doi == paper_doi).first()
        if existing:
            return json.loads(existing.vector)
    finally:
        db.close()
    vec = encode_paper(title, abstract, summary)
    if vec is None:
        return None
    db = SessionLocal()
    try:
        emb = PaperEmbedding(
            paper_doi=paper_doi,
            domain=domain,
            vector=json.dumps(vec),
            model_name=MODEL_NAME,
        )
        db.add(emb)
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
    return vec

def encode_user_interest(description: str, keywords: str = "", llm_expanded: str = None) -> list:
    text = llm_expanded or _to_en(description)
    if keywords:
        kws = _to_en(keywords) if _is_chinese(keywords) else keywords
        text = text + ". " + kws
    return encode_text(text)

def cosine_similarity(vec_a: list, vec_b: list) -> float:
    a = np.array(vec_a, dtype=np.float32)
    b = np.array(vec_b, dtype=np.float32)
    return float(np.dot(a, b))
