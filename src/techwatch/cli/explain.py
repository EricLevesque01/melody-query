"""CLI explain command — detailed offer explanation."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from techwatch.persistence.database import get_session, init_db
from techwatch.persistence.repos import OfferRepo

console = Console()


def explain_cmd(
    offer_id: str = typer.Argument(..., help="Offer ID to explain"),
) -> None:
    """Show a detailed explanation of why an offer ranked the way it did.

    Example:
        techwatch explain abc123
    """
    init_db()

    with get_session() as session:
        repo = OfferRepo(session)
        row = repo.get_by_offer_id(offer_id)

        if not row:
            console.print(f"[red]✗ Offer '{offer_id}' not found[/]")
            raise typer.Exit(1)

        # Header
        console.print()
        console.print(
            Panel(
                f"[bold]{row.title}[/]\n"
                f"[dim]{row.marketplace} · {row.condition_canonical} · {row.seller_type}[/]",
                title=f"Offer {offer_id}",
                border_style="cyan",
            )
        )

        # Pricing
        console.print("\n[bold cyan]💰 Pricing[/]")
        if row.list_amount:
            console.print(f"   List:     {row.currency} {row.list_amount:.2f}")
        if row.sale_amount:
            console.print(f"   Sale:     {row.currency} {row.sale_amount:.2f}")
        console.print(f"   Shipping: {row.currency} {row.shipping_amount:.2f}")
        if row.total_landed_cost:
            console.print(f"   [bold]Total:   {row.currency} {row.total_landed_cost:.2f}[/]")

        # Condition
        console.print("\n[bold cyan]📦 Condition[/]")
        console.print(f"   Canonical:   {row.condition_canonical}")
        console.print(f"   Source:      {row.condition_source_label or '—'}")
        console.print(f"   Functional:  {row.functional_state}")
        console.print(f"   Cosmetic:    {row.cosmetic_grade}")

        # Score components
        console.print("\n[bold cyan]📊 Score Breakdown[/]")
        if row.score_components_json:
            components = json.loads(row.score_components_json)
            weights = {"spec_fit": 0.35, "value": 0.30, "delivery": 0.15, "condition": 0.10, "trust": 0.10}
            for key, raw in components.items():
                weight = weights.get(key, 0)
                weighted = raw * weight
                bar_len = int(raw * 20)
                bar = "█" * bar_len + "░" * (20 - bar_len)
                console.print(
                    f"   {key:<12} {bar} {raw:.2f} × {weight:.0%} = {weighted:.3f}"
                )
        if row.overall_score is not None:
            console.print(f"\n   [bold]Overall: {row.overall_score:.3f}[/]")

        # Explanation
        if row.explanation:
            console.print("\n[bold cyan]💡 Explanation[/]")
            console.print(Panel(row.explanation, border_style="dim"))

        # Price history summary
        stats = repo.get_price_stats(offer_id, days=30)
        if stats["count"] and stats["count"] > 1:
            console.print("\n[bold cyan]📈 30-Day Price History[/]")
            console.print(f"   Min:    {row.currency} {stats['min']:.2f}")
            console.print(f"   Max:    {row.currency} {stats['max']:.2f}")
            console.print(f"   Median: {row.currency} {stats['median']:.2f}")
            console.print(f"   Points: {stats['count']}")

        console.print()
