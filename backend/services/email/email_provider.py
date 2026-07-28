"""
Email provider: auto-selects backend from config
  SendGrid (free tier) → SMTP → Resend (fallback)
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config.settings import settings

SENDGRID_API_KEY = settings.get("SENDGRID_API_KEY", "")
SMTP_HOST = settings.SMTP_HOST
SMTP_PORT = settings.SMTP_PORT
SMTP_USER = settings.SMTP_USER
SMTP_PASSWORD = settings.get("SMTP_PASSWORD", "")
RESEND_API_KEY = settings.get("RESEND_API_KEY", "")
DEFAULT_FROM = settings.SMTP_FROM


def _send_via_sendgrid(to_email: str, subject: str, html: str) -> dict:
    if not SENDGRID_API_KEY:
        return {"status": "error", "provider": "sendgrid", "message": "Not configured"}
    import requests
    try:
        resp = requests.post(
            "https://api.sendgrid.com/v3/mail/send",
            headers={
                "Authorization": f"Bearer {SENDGRID_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": DEFAULT_FROM},
                "subject": subject,
                "content": [{"type": "text/html", "value": html}],
            },
            timeout=30,
        )
        if resp.status_code in (200, 201, 202):
            return {"status": "success", "provider": "sendgrid", "message": "sent"}
        return {"status": "error", "provider": "sendgrid", "message": resp.text}
    except Exception as e:
        return {"status": "error", "provider": "sendgrid", "message": str(e)}


def _send_via_smtp(to_email: str, subject: str, html: str = "", text: str = "") -> dict:
    if not SMTP_HOST or not SMTP_USER:
        return {"status": "error", "provider": "smtp", "message": "SMTP not configured"}
    msg = MIMEMultipart("alternative")
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    if text:
        msg.attach(MIMEText(text, "plain", "utf-8"))
    if html:
        msg.attach(MIMEText(html, "html", "utf-8"))
    if not text and not html:
        msg.attach(MIMEText("", "plain", "utf-8"))
    try:
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_USER, [to_email], msg.as_string())
        return {"status": "success", "provider": "smtp", "message": "sent"}
    except Exception as e:
        return {"status": "error", "provider": "smtp", "message": str(e)}


def _send_via_resend(to_email: str, subject: str, html: str) -> dict:
    if not RESEND_API_KEY:
        return {"status": "error", "provider": "resend", "message": "Not configured"}
    import requests
    try:
        resp = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": DEFAULT_FROM,
                "to": [to_email],
                "subject": subject,
                "html": html,
            },
            timeout=30,
        )
        if resp.status_code in (200, 201):
            return {"status": "success", "provider": "resend", "message": "sent"}
        return {"status": "error", "provider": "resend", "message": resp.text}
    except Exception as e:
        return {"status": "error", "provider": "resend", "message": str(e)}


def send_email(to_email: str, subject: str, html_content: str = "", text_content: str = "") -> dict:
    """Auto-select email backend: SendGrid → SMTP → Resend"""
    if SENDGRID_API_KEY:
        result = _send_via_sendgrid(to_email, subject, html_content)
        if result["status"] == "success":
            return result
        print(f"[Email] SendGrid failed: {result['message']}")

    result = _send_via_smtp(to_email, subject, html_content, text_content)
    if result["status"] == "success":
        return result
    print(f"[Email] SMTP failed: {result['message']}")

    if RESEND_API_KEY:
        result = _send_via_resend(to_email, subject, html_content)
        if result["status"] == "success":
            return result
        print(f"[Email] Resend failed: {result['message']}")

    return result
