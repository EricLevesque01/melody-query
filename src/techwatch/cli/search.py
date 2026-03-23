"""CLI search command — intent-driven product search."""

from __future__ import annotations

from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from techwatch.config import get_settings
from techwatch.models import SearchQuery
from techwatch.models.enums import CanonicalCondition
from techwatch.persistence.database import get_session, init_db

console = Console()


def search_cmd(
    query: str = typer.Argument(..., help="Natural language search query"),
    budget: Optional[float] = typer.Option(None, "--budget", "-b", help="Maximum budget"),
    country: Optional[str] = typer.Option(None, "--country", "-c", help="Country code (e.g., US)"),
    postal_code: Optional[str] = typer.Option(
        None, "--postal-code", "-p", help="Postal/ZIP code for delivery estimates"
    ),
    currency: Optional[str] = typer.Option(None, "--currency", help="Display currency (e.g., USD)"),
    conditions: Optional[str] = typer.Option(
        None,
        "--conditions",
        help="Comma-separated conditions: new,open_box,refurbished,used_good,used_fair",
    ),
    top: int = typer.Option(10, "--top", "-n", help="Number of results to show"),
) -> None:
    """Search for tech products across all sources.

    Examples:
        techwatch search "used thinkpad x1 carbon" --budget 900
        techwatch search "OLED monitor USB-C" --conditions new,open_box --top 5
    """
    settings = get_settings()
    init_db()

    # Parse conditions
    condition_list = []
    if conditions:
        for c in conditions.split(","):
            c = c.strip()
            try:
                condition_list.append(CanonicalCondition(c))
            except ValueError:
                console.print(f"[yellow]⚠ Unknown condition '{c}', skipping[/]")

    search_query = SearchQuery(
        raw_query=query,
        budget=budget,
        country=country or settings.country,
        postal_code=postal_code,
        currency=currency or settings.currency,
        conditions=condition_list or list(CanonicalCondition),
        top_n=top,
    )

    console.print(f"\n[bold cyan]Searching:[/] {query}")
    if budget:
        console.print(f"   [dim]Budget: {search_query.currency} {budget:.2f}[/]")
    location_str = f"   [dim]Location: {search_query.country}"
    if postal_code:
        location_str += f" {postal_code}"
    location_str += "[/]"
    console.print(location_str)
    console.print(f"   [dim]Conditions: {', '.join(c.value for c in search_query.conditions)}[/]")
    console.print()

    # Run the search orchestrator
    from techwatch.agents.orchestrator import SearchOrchestrator

    has_openai = bool(get_settings().openai_api_key.get_secret_value())
    orchestrator = SearchOrchestrator(skip_llm=not has_openai)

    try:
        response = orchestrator.search(search_query)
    except Exception as e:
        console.print(f"[red]Search failed: {e}[/]")
        raise typer.Exit(1)
    finally:
        orchestrator.close()

    if response.errors:
        for err in response.errors:
            # Truncate verbose HTTP error URLs for clean CLI display
            display = err
            if "for url" in display:
                display = display.split("for url")[0].strip().rstrip("'")
            console.print(f"[yellow]⚠ {display}[/]")

    if not response.results:
        console.print("[dim]No results found. Try broadening your search.[/]")
        return

    # Display results
    table = Table(title=f"Top {len(response.results)} Results (of {response.total_found} found)")
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", width=35)
    table.add_column("Condition", width=12)
    table.add_column("Price", width=12, justify="right")
    table.add_column("Total", width=12, justify="right")
    table.add_column("Score", width=7, justify="right")
    table.add_column("Source", width=10)

    for r in response.results:
        table.add_row(
            str(r.rank),
            r.product.title[:33] + (".." if len(r.product.title) > 33 else ""),
            r.offer.condition.canonical.value,
            f"{r.offer.pricing.currency} {r.offer.pricing.effective_price:.2f}",
            f"{r.offer.pricing.currency} {r.offer.pricing.total_landed_cost:.2f}",
            f"{r.analysis.overall_score:.3f}",
            r.offer.source.value,
        )

    console.print(table)

    if response.plan and response.plan.reasoning:
        console.print(f"\n[dim]Plan: {response.plan.reasoning}[/]")
    console.print()
