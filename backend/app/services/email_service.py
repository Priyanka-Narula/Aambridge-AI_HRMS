"""Email helpers for sharing candidate profiles with clients."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from fastapi import HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


def email_configured() -> bool:
    return bool(settings.SMTP_HOST and (settings.SMTP_FROM or settings.SMTP_USER))


def send_email_with_attachment(
    *,
    to_emails: list[str],
    subject: str,
    body_text: str,
    attachment_bytes: bytes | None = None,
    attachment_filename: str | None = None,
    attachment_mime: str = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
) -> dict:
    """Send an email via SMTP. Raises HTTPException if mail is not configured or send fails."""
    if not email_configured():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Email is not configured. Set SMTP_HOST and SMTP_FROM in backend/.env, "
                "or download the Excel and share it manually."
            ),
        )

    recipients = [e.strip() for e in to_emails if e and e.strip()]
    if not recipients:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one recipient email is required",
        )

    from_addr = (settings.SMTP_FROM or settings.SMTP_USER or "").strip()
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = ", ".join(recipients)
    msg.set_content(body_text)

    if attachment_bytes and attachment_filename:
        maintype, _, subtype = attachment_mime.partition("/")
        msg.add_attachment(
            attachment_bytes,
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=attachment_filename,
        )

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=30) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
    except Exception as exc:
        logger.exception("Failed to send email to %s", recipients)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send email: {exc}",
        ) from exc

    return {
        "sent_to": recipients,
        "subject": subject,
        "attachment": attachment_filename,
    }
