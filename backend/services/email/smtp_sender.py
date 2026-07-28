import os

from services.email.daily_email import build_daily_email
from services.config.subscription import load_subscription
from services.email.email_provider import send_email

SMTP_USER = os.getenv("SMTP_USER", "")


def send_email_to(
    to_email: str,
    subject: str,
    html_content: str = "",
    text_content: str = "",
) -> dict:
    """Send an email using dual provider (Resend primary, SMTP fallback)"""
    return send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content,
        text_content=text_content,
    )


def send_daily_email() -> dict:
    config = load_subscription()
    to_email = config.get("email", "")
    if not to_email:
        return {"status": "error", "message": "No recipient email configured"}

    html_content = build_daily_email()
    return send_email_to(
        to_email=to_email,
        subject="ChemVigil Daily Literature Recommendation",
        html_content=html_content,
    )
