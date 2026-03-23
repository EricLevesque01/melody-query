"""CLI email commands — test email delivery."""

from __future__ import annotations

import typer
from rich.console import Console

from techwatch.config import get_settings

console = Console()
email_app = typer.Typer(no_args_is_help=True)


@email_app.command("test")
def email_test(
    to: str = typer.Option(None, "--to", help="Recipient email (defaults to config)"),
) -> None:
    """Send a test email to verify SMTP configuration.

    Example:
        techwatch email test --to user@example.com
    """
    settings = get_settings()
    recipient = to or settings.email_from

    console.print(f"\n[cyan]Sending test email to {recipient} ...[/]")
    console.print(f"   SMTP: {settings.smtp.host}:{settings.smtp.port}")
    console.print(f"   TLS:  {settings.smtp.use_tls}")

    from techwatch.email.smtp import send_email

    try:
        send_email(
            to=recipient,
            subject="TechWatch - Test Email",
            body=(
                "This is a test email from TechWatch.\n\n"
                "If you received this, your SMTP configuration is working.\n\n"
                "-- TechWatch"
            ),
        )
        console.print(f"   [green]Email sent successfully[/]")
    except Exception as e:
        console.print(f"   [red]Send failed: {e}[/]")
        raise typer.Exit(1)

    console.print()
