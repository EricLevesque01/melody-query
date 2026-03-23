"""CLI compare command — side-by-side offer comparison."""

from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

from techwatch.persistence.database import get_session, init_db
from techwatch.persistence.repos import OfferRepo

console = Console()


def compare_cmd(
    offer_id_1: str = typer.Argument(..., help="First offer ID"),
    offer_id_2: str = typer.Argument(..., help="Second offer ID"),
) -> None:
    """Compare two offers side by side.

    Example:
        techwatch compare abc123 def456
    """
    init_db()

    with get_session() as session:
        repo = OfferRepo(session)
        row1 = repo.get_by_offer_id(offer_id_1)
        row2 = repo.get_by_offer_id(offer_id_2)

        if not row1:
            console.print(f"[red]✗ Offer '{offer_id_1}' not found[/]")
            raise typer.Exit(1)
        if not row2:
            console.print(f"[red]✗ Offer '{offer_id_2}' not found[/]")
            raise typer.Exit(1)

        table = Table(title="Offer Comparison", show_lines=True)
        table.add_column("Field", style="cyan", width=20)
        table.add_column(offer_id_1[:12], width=30)
        table.add_column(offer_id_2[:12], width=30)

        fields = [
            ("Title", "title"),
            ("Brand", "brand"),
            ("Condition", "condition_canonical"),
            ("Cosmetic", "cosmetic_grade"),
            ("Functional", "functional_state"),
            ("List Price", "list_amount"),
            ("Sale Price", "sale_amount"),
            ("Shipping", "shipping_amount"),
            ("Total Cost", "total_landed_cost"),
            ("Marketplace", "marketplace"),
            ("Seller", "seller_name"),
            ("Score", "overall_score"),
        ]

        for label, attr in fields:
            v1 = str(getattr(row1, attr, "—") or "—")
            v2 = str(getattr(row2, attr, "—") or "—")
            table.add_row(label, v1, v2)

        console.print(table)
