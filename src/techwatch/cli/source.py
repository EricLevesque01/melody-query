"""CLI source commands — test adapter connectivity."""

from __future__ import annotations

import typer
from rich.console import Console

from techwatch.config import get_settings

console = Console()
source_app = typer.Typer(no_args_is_help=True)


@source_app.command("test")
def source_test(
    source_name: str = typer.Argument(
        ..., help="Source adapter to test: bestbuy, ebay, structured"
    ),
) -> None:
    """Test connectivity and authentication for a source adapter.

    Examples:
        techwatch source test bestbuy
        techwatch source test ebay
    """
    settings = get_settings()

    console.print(f"\n[cyan]Testing {source_name} adapter ...[/]")

    if source_name == "bestbuy":
        key = settings.bestbuy_api_key.get_secret_value()
        if not key:
            console.print("[red]BESTBUY_API_KEY not set[/]")
            raise typer.Exit(1)
        console.print(f"   API Key: {'*' * 4}{key[-4:]}")

        try:
            from techwatch.adapters.bestbuy.categories import BestBuyCategoriesAdapter

            with BestBuyCategoriesAdapter() as adapter:
                cats = adapter.get_top_level()
            console.print(f"   [green]Connected - {len(cats)} top-level categories[/]")
        except Exception as e:
            console.print(f"   [red]Connection failed: {e}[/]")
            raise typer.Exit(1)

    elif source_name == "ebay":
        client_id = settings.ebay_client_id.get_secret_value()
        if not client_id:
            console.print("[red]EBAY_CLIENT_ID not set[/]")
            raise typer.Exit(1)
        console.print(f"   Client ID: {'*' * 4}{client_id[-4:]}")

        try:
            from techwatch.adapters.ebay.auth import EbayAuth

            auth = EbayAuth()
            token = auth.get_token()
            auth.close()
            console.print(f"   [green]OAuth token acquired ({len(token)} chars)[/]")
        except Exception as e:
            console.print(f"   [red]OAuth failed: {e}[/]")
            raise typer.Exit(1)

    elif source_name == "structured":
        console.print("   [green]Structured data adapter requires no credentials[/]")

        try:
            from techwatch.adapters.structured.jsonld import JsonLdExtractor

            with JsonLdExtractor() as adapter:
                console.print("   [green]JSON-LD extractor ready[/]")
        except Exception as e:
            console.print(f"   [red]Extractor init failed: {e}[/]")
            raise typer.Exit(1)

    elif source_name == "fx":
        try:
            from techwatch.adapters.fx.ecb import EcbRatesAdapter

            with EcbRatesAdapter() as adapter:
                rates = adapter.get_rates()
            console.print(f"   [green]ECB rates loaded: {len(rates)} currencies[/]")
        except Exception as e:
            console.print(f"   [red]ECB fetch failed: {e}[/]")
            raise typer.Exit(1)

    else:
        console.print(f"[red]Unknown source '{source_name}'[/]")
        console.print("[dim]Available: bestbuy, ebay, structured, fx[/]")
        raise typer.Exit(1)

    console.print()
