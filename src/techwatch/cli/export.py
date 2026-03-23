"""CLI export command — export watch results to CSV or JSON."""

from __future__ import annotations

import csv
import json
import sys
from io import StringIO

import typer
from rich.console import Console

from techwatch.persistence.database import get_session, init_db
from techwatch.persistence.repos import OfferRepo, WatchRepo
from techwatch.persistence.tables import OfferRow

console = Console()


def export_cmd(
    watch_id: str = typer.Argument(..., help="Watch ID to export results for"),
    format: str = typer.Option("csv", "--format", "-f", help="Output format: csv, json"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path (default: stdout)"),
) -> None:
    """Export watch results to a file.

    Example:
        techwatch export abc123 --format csv --output results.csv
        techwatch export abc123 --format json
    """
    init_db()

    with get_session() as session:
        watch_repo = WatchRepo(session)
        watch = watch_repo.get(watch_id)

        if not watch:
            console.print(f"[red]Watch '{watch_id}' not found[/]")
            raise typer.Exit(1)

        # Query all offers that match the watch's query term
        offers = (
            session.query(OfferRow)
            .filter(OfferRow.title.ilike(f"%{watch.raw_query}%"))
            .order_by(OfferRow.overall_score.desc())
            .all()
        )

        if not offers:
            console.print("[dim]No results found for this watch.[/]")
            return

    # Export
    if format.lower() == "json":
        data = [_offer_to_dict(o) for o in offers]
        text = json.dumps(data, indent=2, default=str)
    else:
        text = _offers_to_csv(offers)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(text)
        console.print(f"[green]Exported {len(offers)} results to {output}[/]")
    else:
        console.print(text)


def _offer_to_dict(row: OfferRow) -> dict:
    return {
        "offer_id": row.offer_id,
        "source": row.source,
        "title": row.title,
        "brand": row.brand,
        "category": row.canonical_category,
        "condition": row.condition_canonical,
        "condition_source": row.condition_source_label,
        "functional_state": row.functional_state,
        "cosmetic_grade": row.cosmetic_grade,
        "list_price": row.list_amount,
        "sale_price": row.sale_amount,
        "shipping": row.shipping_amount,
        "total_cost": row.total_landed_cost,
        "currency": row.currency,
        "seller": row.seller_name,
        "marketplace": row.marketplace,
        "score": row.overall_score,
        "url": row.url,
        "observed_at": str(row.observed_at) if row.observed_at else None,
    }


def _offers_to_csv(offers: list[OfferRow]) -> str:
    if not offers:
        return ""

    buf = StringIO()
    fields = [
        "offer_id", "source", "title", "brand", "category",
        "condition", "functional_state", "cosmetic_grade",
        "sale_price", "shipping", "total_cost", "currency",
        "seller", "marketplace", "score", "url",
    ]
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()

    for o in offers:
        writer.writerow({
            "offer_id": o.offer_id,
            "source": o.source,
            "title": o.title,
            "brand": o.brand,
            "category": o.canonical_category,
            "condition": o.condition_canonical,
            "functional_state": o.functional_state,
            "cosmetic_grade": o.cosmetic_grade,
            "sale_price": o.sale_amount,
            "shipping": o.shipping_amount,
            "total_cost": o.total_landed_cost,
            "currency": o.currency,
            "seller": o.seller_name,
            "marketplace": o.marketplace,
            "score": o.overall_score,
            "url": o.url,
        })

    return buf.getvalue()
