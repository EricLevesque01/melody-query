"""Digest renderer — formats alert data into email-ready text.

Uses Babel for locale-aware currency formatting and zoneinfo for timezone rendering.
"""

from __future__ import annotations

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from babel.numbers import format_currency

from techwatch.models.narrative import DigestEntry, DigestPayload

logger = logging.getLogger(__name__)


def render_digest(
    payload: DigestPayload,
    *,
    locale: str = "en_US",
    timezone: str = "America/New_York",
) -> tuple[str, str]:
    """Render a digest payload into (subject, plaintext body).

    Returns:
        Tuple of (email subject line, plaintext email body).
    """
    subject = f"TechWatch Alert: {payload.watch_query}"
    if len(payload.entries) == 1:
        subject += f" - {payload.entries[0].headline}"

    lines: list[str] = []
    lines.append(f"TechWatch Deal Alert")
    lines.append(f"{'=' * 50}")
    lines.append(f"Watch: {payload.watch_query}")
    lines.append(f"Generated: {payload.generated_at_display}")
    lines.append("")

    if payload.summary:
        lines.append(f"Summary: {payload.summary}")
        lines.append("")

    lines.append(f"{'─' * 50}")

    for i, entry in enumerate(payload.entries, 1):
        lines.append(f"")
        lines.append(f"  #{i} {entry.title}")
        lines.append(f"     Price:     {entry.price_display}")
        lines.append(f"     Condition: {entry.condition_display}")
        lines.append(f"     Reason:    {entry.trigger_reason}")
        if entry.url:
            lines.append(f"     Link:      {entry.url}")
        lines.append(f"     {entry.headline}")
        lines.append(f"")

    lines.append(f"{'─' * 50}")
    lines.append("")
    lines.append("To stop these alerts, pause or delete the watch:")
    lines.append(f"  techwatch watch pause {payload.watch_id}")
    lines.append(f"  techwatch watch delete {payload.watch_id}")
    lines.append("")
    lines.append("— TechWatch")

    body = "\n".join(lines)
    return subject, body


def render_digest_html(
    payload: DigestPayload,
    *,
    locale: str = "en_US",
    timezone: str = "America/New_York",
) -> str:
    """Render a digest payload into an HTML email body."""
    entries_html = ""
    for i, entry in enumerate(payload.entries, 1):
        link = f'<a href="{entry.url}">View</a>' if entry.url else ""
        entries_html += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee">{i}</td>
            <td style="padding:8px;border-bottom:1px solid #eee">
                <strong>{entry.title}</strong><br>
                <small>{entry.condition_display}</small>
            </td>
            <td style="padding:8px;border-bottom:1px solid #eee;text-align:right">
                <strong>{entry.price_display}</strong>
            </td>
            <td style="padding:8px;border-bottom:1px solid #eee">{entry.trigger_reason}</td>
            <td style="padding:8px;border-bottom:1px solid #eee">{link}</td>
        </tr>
        """

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto">
        <h2 style="color:#2563eb">TechWatch Deal Alert</h2>
        <p><strong>Watch:</strong> {payload.watch_query}</p>
        <p><strong>Generated:</strong> {payload.generated_at_display}</p>
        {f'<p><em>{payload.summary}</em></p>' if payload.summary else ''}
        <table style="width:100%;border-collapse:collapse">
            <tr style="background:#f1f5f9">
                <th style="padding:8px;text-align:left">#</th>
                <th style="padding:8px;text-align:left">Product</th>
                <th style="padding:8px;text-align:right">Price</th>
                <th style="padding:8px;text-align:left">Alert</th>
                <th style="padding:8px;text-align:left">Link</th>
            </tr>
            {entries_html}
        </table>
        <hr style="margin:20px 0">
        <p style="font-size:12px;color:#6b7280">
            To stop these alerts: <code>techwatch watch pause {payload.watch_id}</code>
        </p>
    </body>
    </html>
    """
