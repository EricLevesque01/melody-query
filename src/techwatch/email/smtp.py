"""SMTP email adapter — replaceable email delivery backend."""

from __future__ import annotations

import logging
import smtplib
from email.message import EmailMessage

from techwatch.config import get_settings

logger = logging.getLogger(__name__)


def send_email(
    *,
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
) -> None:
    """Send an email via the configured SMTP server."""
    settings = get_settings()

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.email_from
    msg["To"] = to
    msg.set_content(body)

    if html_body:
        msg.add_alternative(html_body, subtype="html")

    # Add unsubscribe header (CAN-SPAM compliance awareness)
    msg["List-Unsubscribe"] = f"<mailto:{settings.email_from}?subject=unsubscribe>"

    smtp_settings = settings.smtp

    try:
        if smtp_settings.use_tls:
            server = smtplib.SMTP(smtp_settings.host, smtp_settings.port)
            server.starttls()
        else:
            server = smtplib.SMTP(smtp_settings.host, smtp_settings.port)

        if smtp_settings.username and smtp_settings.password:
            server.login(
                smtp_settings.username,
                smtp_settings.password.get_secret_value(),
            )

        server.send_message(msg)
        server.quit()
        logger.info("Email sent to %s: %s", to, subject)

    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        raise


class MockEmailAdapter:
    """In-memory email adapter for testing."""

    def __init__(self) -> None:
        self.sent: list[dict[str, str]] = []

    def send(
        self, *, to: str, subject: str, body: str, html_body: str | None = None
    ) -> None:
        self.sent.append({
            "to": to,
            "subject": subject,
            "body": body,
            "html_body": html_body or "",
        })
