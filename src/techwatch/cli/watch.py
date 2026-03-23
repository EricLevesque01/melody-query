"""CLI watch commands — create, list, pause, resume, delete saved watches."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from techwatch.config import get_settings
from techwatch.models import Watch, WatchTrigger
from techwatch.models.enums import (
    CanonicalCondition,
    TriggerMetric,
    TriggerOperator,
    WatchStatus,
)
from techwatch.persistence.database import get_session, init_db
from techwatch.persistence.repos import WatchRepo

console = Console()
watch_app = typer.Typer(no_args_is_help=True)


def _parse_triggers(trigger_str: str) -> list[WatchTrigger]:
    """Parse trigger expressions like 'price_drop_pct>=8 OR new_offer_rank<=3'."""
    triggers = []
    parts = [p.strip() for p in trigger_str.replace(" OR ", "|").replace(" AND ", "|").split("|")]

    for part in parts:
        for op_str, op_enum in [(">=", TriggerOperator.GTE), ("<=", TriggerOperator.LTE),
                                 (">", TriggerOperator.GT), ("<", TriggerOperator.LT),
                                 ("==", TriggerOperator.EQ)]:
            if op_str in part:
                metric_str, value_str = part.split(op_str, 1)
                try:
                    metric = TriggerMetric(metric_str.strip())
                    triggers.append(WatchTrigger(
                        metric=metric,
                        operator=op_enum,
                        threshold=float(value_str.strip()),
                    ))
                except (ValueError, KeyError):
                    console.print(f"[yellow]⚠ Could not parse trigger '{part}'[/]")
                break

    return triggers


@watch_app.command("create")
def watch_create(
    query: str = typer.Argument(..., help="Natural language search query"),
    budget: Optional[float] = typer.Option(None, "--budget", "-b", help="Maximum budget"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Country code"),
    postal_code: Optional[str] = typer.Option(None, "--postal-code", "-p", help="Postal code"),
    currency: Optional[str] = typer.Option(None, "--currency", help="Currency"),
    conditions: Optional[str] = typer.Option(None, "--conditions", help="Comma-separated conditions"),
    top: int = typer.Option(10, "--top", "-n", help="Max results per run"),
    schedule: str = typer.Option("0 9 * * *", "--schedule", "-s", help="Cron expression"),
    timezone: Optional[str] = typer.Option(None, "--timezone", "-tz", help="IANA timezone"),
    email: Optional[str] = typer.Option(None, "--email", "-e", help="Alert email address"),
    trigger: Optional[str] = typer.Option(None, "--trigger", "-t", help="Trigger expression"),
) -> None:
    """Create a new saved watch.

    Example:
        techwatch watch create "oled monitor 27 240hz" --budget 650 --schedule "0 9 * * *" --email user@example.com
    """
    settings = get_settings()
    init_db()

    condition_list = []
    if conditions:
        for c in conditions.split(","):
            try:
                condition_list.append(CanonicalCondition(c.strip()))
            except ValueError:
                console.print(f"[yellow]⚠ Unknown condition '{c.strip()}'[/]")

    triggers = _parse_triggers(trigger) if trigger else []

    watch = Watch(
        raw_query=query,
        budget=budget,
        country=country or settings.country,
        postal_code=postal_code,
        currency=currency or settings.currency,
        conditions=condition_list or list(CanonicalCondition),
        top_n=top,
        schedule=schedule,
        timezone=timezone or settings.timezone,
        email=email,
        triggers=triggers,
    )

    with get_session() as session:
        repo = WatchRepo(session)
        row = repo.create(watch)

    console.print(f"\n[bold green]✓ Watch created:[/] {watch.watch_id}")
    console.print(f"  Query:    {query}")
    console.print(f"  Schedule: {schedule} ({watch.timezone})")
    if email:
        console.print(f"  Email:    {email}")
    if triggers:
        console.print(f"  Triggers: {len(triggers)} rule(s)")
    console.print()


@watch_app.command("list")
def watch_list() -> None:
    """List all saved watches."""
    init_db()

    with get_session() as session:
        repo = WatchRepo(session)
        watches = repo.list_all()

        if not watches:
            console.print("[dim]No watches found. Create one with 'techwatch watch create'.[/]")
            return

        table = Table(title="Saved Watches")
        table.add_column("ID", style="cyan", width=14)
        table.add_column("Query", width=30)
        table.add_column("Status", width=10)
        table.add_column("Schedule", width=14)
        table.add_column("Email", width=20)
        table.add_column("Last Run", width=20)

        for w in watches:
            status_style = {"active": "green", "paused": "yellow", "deleted": "red"}
            table.add_row(
                w.watch_id,
                w.raw_query[:28] + ("…" if len(w.raw_query) > 28 else ""),
                f"[{status_style.get(w.status, 'dim')}]{w.status}[/]",
                w.schedule,
                w.email or "—",
                str(w.last_run_at.strftime("%Y-%m-%d %H:%M") if w.last_run_at else "—"),
            )

        console.print(table)


@watch_app.command("pause")
def watch_pause(
    watch_id: str = typer.Argument(..., help="Watch ID to pause"),
) -> None:
    """Pause a saved watch."""
    init_db()
    with get_session() as session:
        repo = WatchRepo(session)
        if repo.update_status(watch_id, WatchStatus.PAUSED):
            console.print(f"[yellow]⏸ Watch {watch_id} paused[/]")
        else:
            console.print(f"[red]✗ Watch '{watch_id}' not found[/]")
            raise typer.Exit(1)


@watch_app.command("resume")
def watch_resume(
    watch_id: str = typer.Argument(..., help="Watch ID to resume"),
) -> None:
    """Resume a paused watch."""
    init_db()
    with get_session() as session:
        repo = WatchRepo(session)
        if repo.update_status(watch_id, WatchStatus.ACTIVE):
            console.print(f"[green]▶ Watch {watch_id} resumed[/]")
        else:
            console.print(f"[red]✗ Watch '{watch_id}' not found[/]")
            raise typer.Exit(1)


@watch_app.command("delete")
def watch_delete(
    watch_id: str = typer.Argument(..., help="Watch ID to delete"),
    confirm: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
) -> None:
    """Delete a saved watch."""
    init_db()
    if not confirm:
        typer.confirm(f"Delete watch {watch_id}?", abort=True)

    with get_session() as session:
        repo = WatchRepo(session)
        if repo.update_status(watch_id, WatchStatus.DELETED):
            console.print(f"[red]🗑 Watch {watch_id} deleted[/]")
        else:
            console.print(f"[red]✗ Watch '{watch_id}' not found[/]")
            raise typer.Exit(1)
