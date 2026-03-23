"""TechWatch CLI — main Typer application and entry point."""

from __future__ import annotations

import typer
from rich.console import Console

from techwatch import __version__

console = Console()

app = typer.Typer(
    name="techwatch",
    help="Agentic CLI tech purchase research assistant",
    no_args_is_help=True,
    rich_markup_mode="rich",
    add_completion=True,
)


def version_callback(value: bool) -> None:
    if value:
        console.print(f"[bold cyan]techwatch[/] v{__version__}")
        raise typer.Exit()


@app.callback()
def main_callback(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-V",
        help="Enable verbose logging (debug mode).",
    ),
) -> None:
    """TechWatch — research tech products, track prices, get deal alerts."""
    import logging

    if verbose:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        )
    else:
        # Suppress verbose adapter/orchestrator logs in normal mode
        logging.basicConfig(level=logging.CRITICAL)


# ── Register sub-command groups ─────────────────────────────────────

from techwatch.cli.search import search_cmd  # noqa: E402
from techwatch.cli.compare import compare_cmd  # noqa: E402
from techwatch.cli.explain import explain_cmd  # noqa: E402
from techwatch.cli.watch import watch_app  # noqa: E402
from techwatch.cli.run import run_app  # noqa: E402
from techwatch.cli.source import source_app  # noqa: E402
from techwatch.cli.email_cmd import email_app  # noqa: E402
from techwatch.cli.export import export_cmd  # noqa: E402

app.command(name="search")(search_cmd)
app.command(name="compare")(compare_cmd)
app.command(name="explain")(explain_cmd)
app.add_typer(watch_app, name="watch", help="Manage saved watches")
app.add_typer(run_app, name="run", help="Execute watches")
app.add_typer(source_app, name="source", help="Test source adapters")
app.add_typer(email_app, name="email", help="Email utilities")
app.command(name="export")(export_cmd)


def main() -> None:
    """Console script entry point."""
    app()


if __name__ == "__main__":
    main()
