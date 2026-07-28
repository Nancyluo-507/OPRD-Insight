from fastapi import APIRouter, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from database.session import SessionLocal
from database.models import User
from database.crud import get_user, get_user_by_name, create_user, verify_user_email
from utils.helpers import row_to_dict, hash_password, verify_password, create_token, verify_token
from utils.exceptions import AppException
from utils.logger import log
from config.settings import settings
import hashlib

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

VERIFY_HTML = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>Email Verification - ChemVigil</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:linear-gradient(135deg,#0f172a,#1e3a5f);min-height:100vh;display:flex;align-items:center;justify-content:center;}}
.card{{background:white;border-radius:24px;padding:50px 40px;text-align:center;max-width:420px;width:90%;box-shadow:0 30px 80px rgba(0,0,0,.3);animation:fadeIn .6s ease;}}
.icon{{font-size:64px;margin-bottom:16px;}}
h1{{font-size:24px;color:#0f172a;margin-bottom:10px;}}
p{{font-size:15px;color:#64748b;line-height:1.7;margin-bottom:24px;}}
.btn{{display:inline-block;padding:12px 32px;background:#2456c3;color:white;border-radius:12px;text-decoration:none;font-weight:600;font-size:15px;transition:.2s;}}
.btn:hover{{background:#1d4ed8;transform:translateY(-2px);}}
.error h1{{color:#dc2626;}}
@keyframes fadeIn{{from{{opacity:0;transform:translateY(20px);}}to{{opacity:1;transform:translateY(0);}}}}
</style></head>
<body><div class="card {status}">
<div class="icon">{icon}</div>
<h1>{title}</h1>
<p>{message}</p>
<a class="btn" href="/app">Go to ChemVigil</a>
</div></body></html>"""


class RegisterBody(BaseModel):
    name: str
    password: str
    email: str = ""


class LoginBody(BaseModel):
    name: str
    password: str


def _get_current_user(authorization: str | None) -> dict | None:
    if not authorization or not authorization.startswith("Bearer "):
        return None
    uid = verify_token(authorization[7:])
    if not uid:
        return None
    return get_user(uid)


def _send_verify_email(to_email: str, verify_token: str, user_name: str):
    from services.email.email_provider import send_email
    link = f"{settings.PUBLIC_URL}/api/v1/auth/verify-email?token={verify_token}"
    html = f"""<!DOCTYPE html>
<html><body style="font-family:Arial;padding:40px;background:#f5f7fb;">
<div style="max-width:600px;margin:auto;background:white;border-radius:16px;padding:35px;">
<h2 style="color:#2456c3;">Verify your email</h2>
<p>Hi {user_name},</p>
<p>Click the button below to verify your email address:</p>
<p><a href="{link}" style="display:inline-block;padding:12px 24px;background:#2456c3;color:white;border-radius:8px;text-decoration:none;">Verify Email</a></p>
<p>Or copy this link: <br><small>{link}</small></p>
<p style="color:#999;font-size:12px;">This link expires in 24 hours.</p>
</div></body></html>"""
    send_email(to_email, "ChemVigil - Verify your email", html_content=html)


@router.post("/register")
def register(body: RegisterBody):
    if get_user_by_name(body.name):
        raise AppException("Username already exists", 409)
    tmp_token = create_token(0)
    verify_token = hashlib.sha256(f"{body.name}:{tmp_token}".encode()).hexdigest()[:32]
    user = create_user(body.name, hash_password(body.password), body.email, verify_token)
    if body.email:
        try:
            _send_verify_email(body.email, verify_token, user.name)
        except Exception as e:
            log.warning(f"Failed to send verification email: {e}")
    auth_token = create_token(user.id)
    return {"user": row_to_dict(user, exclude=["password_hash"]), "token": auth_token}


@router.post("/login")
def login(body: LoginBody):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.name == body.name).first()
    finally:
        db.close()
    if not user or not verify_password(body.password, user.password_hash):
        raise AppException("Invalid credentials", 401)
    return {"user": row_to_dict(user, exclude=["password_hash"]), "token": create_token(user.id)}


@router.get("/me")
def auth_me(authorization: str = Header(None)):
    user = _get_current_user(authorization) if authorization else None
    if not user:
        raise AppException("Unauthorized", 401)
    return user


@router.post("/resend-verify")
def resend_verify_email(authorization: str = Header(None)):
    user_dict = _get_current_user(authorization) if authorization else None
    if not user_dict:
        raise AppException("Unauthorized", 401)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_dict["id"]).first()
        if not user:
            raise AppException("User not found", 404)
        if not user.target_email:
            raise AppException("No email configured", 400)
        if user.email_verified:
            raise AppException("Email already verified", 400)
        if not user.email_verify_token:
            tmp = create_token(0)
            user.email_verify_token = hashlib.sha256(f"{user.name}:{tmp}".encode()).hexdigest()[:32]
        db.commit()
        _send_verify_email(user.target_email, user.email_verify_token, user.name)
        return {"message": "Verification email resent"}
    finally:
        db.close()


@router.get("/verify-email")
def verify_email(token: str):
    user = verify_user_email(token)
    if not user:
        return HTMLResponse(VERIFY_HTML.format(
            status="error", icon="❌",
            title="Verification Failed",
            message="Invalid or expired verification link. Please register again.",
        ), status_code=400)
    return HTMLResponse(VERIFY_HTML.format(
        status="success", icon="✅",
        title="Email Verified!",
        message="Your email has been verified successfully. You can now close this page and return to the app.",
    ))
