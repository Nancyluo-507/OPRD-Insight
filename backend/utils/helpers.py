import os
import hashlib
import hmac
import base64
import json
from datetime import datetime

from config.settings import settings


def json_safe(val):
    if val is None:
        return None
    try:
        json.dumps(val)
        return val
    except (TypeError, ValueError):
        return str(val)


def row_to_dict(row, exclude=None):
    if not row:
        return None
    d = {c.name: getattr(row, c.name) for c in row.__table__.columns}
    if exclude:
        for k in exclude:
            d.pop(k, None)
    for k, v in d.items():
        if isinstance(v, datetime):
            d[k] = v.isoformat()
    return d


# --- Auth helpers ---

def hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return base64.b64encode(salt + dk).decode()


def verify_password(password: str, stored: str) -> bool:
    try:
        raw = base64.b64decode(stored)
        salt, dk = raw[:16], raw[16:]
        return hmac.compare_digest(dk, hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000))
    except Exception:
        return False


def create_token(user_id: int) -> str:
    payload = json.dumps({"uid": user_id, "exp": (datetime.now().timestamp() + 86400 * settings.JWT_EXPIRY_DAYS)})
    sig = hmac.new(settings.JWT_SECRET.encode(), payload.encode(), "sha256").hexdigest()
    return base64.b64encode(payload.encode()).decode() + "." + sig


def verify_token(token: str) -> int | None:
    try:
        parts = token.split(".")
        payload = base64.b64decode(parts[0]).decode()
        data = json.loads(payload)
        if data["exp"] < datetime.now().timestamp():
            return None
        expected = parts[0] + "." + hmac.new(settings.JWT_SECRET.encode(), payload.encode(), "sha256").hexdigest()
        if not hmac.compare_digest(token, expected):
            return None
        return data["uid"]
    except Exception:
        return None


# --- Rate limiter (in-memory sliding window) ---

import time as _time

_rate_limit_store: dict = {}

def check_rate_limit(key: str, max_requests: int = 30, window_sec: int = 60):
    """Simple sliding window rate limiter. Raises HTTPException 429 if exceeded."""
    now = _time.time()
    window_start = now - window_sec
    if key not in _rate_limit_store:
        _rate_limit_store[key] = []
    timestamps = [t for t in _rate_limit_store[key] if t > window_start]
    if len(timestamps) >= max_requests:
        raise HTTPException(status_code=429, detail=f"Rate limit exceeded. Max {max_requests} requests per {window_sec}s")
    timestamps.append(now)
    _rate_limit_store[key] = timestamps


# --- FastAPI auth dependency ---

from fastapi import Header, Depends, HTTPException

def require_auth(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    uid = verify_token(authorization[7:])
    if not uid:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return uid



