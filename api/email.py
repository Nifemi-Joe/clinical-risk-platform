"""
Email sending. HONEST STATUS: this does NOT send real email in this
environment - there are no SMTP/API credentials configured, and I'm not
going to fabricate delivery that isn't happening.

What this DOES do: implement the real integration point with the correct
interface, so wiring in a real provider is a config change, not a rewrite.
In dev mode (no SMTP_HOST set), it logs what would have been sent - visible,
honest, and useful for local testing without lying about delivery.

To make this send real email: set SMTP_HOST, SMTP_PORT, SMTP_USER,
SMTP_PASSWORD, FROM_EMAIL as environment variables (e.g. via SendGrid,
AWS SES, Postmark, or any standard SMTP provider) - no code changes needed.
"""
from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

logger = logging.getLogger("email")
logging.basicConfig(level=logging.INFO)

SMTP_HOST = os.environ.get("SMTP_HOST")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
FROM_EMAIL = os.environ.get("FROM_EMAIL", "no-reply@clinical-risk-platform.local")


def send_email(to: str, subject: str, body: str) -> bool:
    """Returns True if actually sent, False if only logged (dev mode).
    Callers should treat False as 'not delivered', not swallow it silently."""
    if not SMTP_HOST:
        logger.info(
            "[DEV MODE - no SMTP configured, email NOT sent] To: %s | Subject: %s | Body: %s",
            to, subject, body,
        )
        return False

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        if SMTP_USER and SMTP_PASSWORD:
            server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
    logger.info("Email sent to %s: %s", to, subject)
    return True


def new_message_notification(to: str, sender_name: str) -> bool:
    return send_email(
        to=to,
        subject="New message on Clinical Risk Platform",
        body=f"You have a new message from {sender_name}. Log in to view it.",
    )


def password_reset_email(to: str, reset_url: str) -> bool:
    return send_email(
        to=to,
        subject="Reset your Clinical Risk Platform password",
        body=(
            f"A password reset was requested for this account. If this was "
            f"you, use the link below within 30 minutes:\n\n{reset_url}\n\n"
            f"If you didn't request this, you can ignore this email."
        ),
    )
