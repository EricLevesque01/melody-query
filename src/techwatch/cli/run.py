"""CLI run commands — execute watches on-demand or as a daemon."""

from __future__ import annotations

import typer
from rich.console import Console

from techwatch.persistence.database import init_db

console = Console()
run_app = typer.Typer(no_args_is_help=True)


@run_app.command("once")
def run_once(
    watch_id: str = typer.Argument(..., help="Watch ID to execute"),
) -> None:
    """Execute a single watch run immediately.

    Example:
        techwatch run once abc123
    """
    init_db()
    console.print(f"[cyan]Running watch {watch_id} ...[/]")

    from techwatch.scheduling.scheduler import execute_watch

    try:
        status = execute_watch(watch_id)
        if status == "not_found":
            console.print(f"[red]✗ Watch '{watch_id}' not found[/]")
            raise typer.Exit(1)
        elif status == "not_active":
            console.print(f"[yellow]⏸ Watch '{watch_id}' is not active (paused or deleted)[/]")
            raise typer.Exit(1)
        elif status == "error":
            console.print(f"[red]✗ Watch '{watch_id}' search failed (see logs)[/]")
            raise typer.Exit(1)
        else:
            console.print(f"[green]✓ Watch {watch_id} completed[/]")
    except typer.Exit:
        raise
    except Exception as e:
        console.print(f"[red]✗ Watch execution failed: {e}[/]")
        raise typer.Exit(1)


@run_app.command("daemon")
def run_daemon() -> None:
    """Start the background scheduler daemon.

    Loads all active watches, executes them on schedule,
    and sends email digests when alerts trigger.
    """
    init_db()
    console.print("[bold cyan]Starting TechWatch daemon ...[/]")

    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    from techwatch.scheduling.scheduler import start_daemon

    start_daemon()
