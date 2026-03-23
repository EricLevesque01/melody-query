"""eBay Browse API adapter."""

from __future__ import annotations

import logging
from typing import Any, Optional

from techwatch.adapters.base import BaseAdapter
from techwatch.adapters.ebay.auth import EbayAuth

logger = logging.getLogger(__name__)

EBAY_API_BASE = "https://api.ebay.com/buy/browse/v1"


class EbayBrowseAdapter(BaseAdapter):
    """Fetch product listings from the eBay Browse API."""

    source_name = "ebay_browse"
    max_qps = 5.0
    burst = 5
    cache_ttl = 180

    def __init__(self, sandbox: bool = False) -> None:
        super().__init__()
        self._auth = EbayAuth(sandbox=sandbox)
        self._base_url = (
            "https://api.sandbox.ebay.com/buy/browse/v1"
            if sandbox
            else EBAY_API_BASE
        )

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self._auth.get_token()}",
            "Content-Type": "application/json",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        }

    def search(
        self,
        query: str,
        *,
        category_ids: list[str] | None = None,
        filter_conditions: list[str] | None = None,
        price_min: float | None = None,
        price_max: float | None = None,
        sort: str = "price",
        limit: int = 50,
        offset: int = 0,
        buyer_postal_code: str | None = None,
    ) -> dict[str, Any]:
        """Search eBay listings.

        Args:
            query: Search keywords.
            category_ids: Filter by category IDs.
            filter_conditions: e.g. ["NEW", "USED"].
            price_min: Minimum price filter.
            price_max: Maximum price filter.
            sort: Sort order (price, newlyListed, etc.).
            limit: Max results per page.
            offset: Pagination offset.
            buyer_postal_code: For delivery estimates.
        """
        url = f"{self._base_url}/item_summary/search"

        params: dict[str, Any] = {
            "q": query,
            "sort": sort,
            "limit": min(limit, 200),
            "offset": offset,
        }

        # Build filter string
        filters = []
        if filter_conditions:
            condition_str = "|".join(filter_conditions)
            filters.append(f"conditions:{{{condition_str}}}")
        if price_min is not None:
            filters.append(f"price:[{price_min}..],priceCurrency:USD")
        if price_max is not None:
            filters.append(f"price:[..{price_max}],priceCurrency:USD")
        if filters:
            params["filter"] = ",".join(filters)

        if category_ids:
            params["category_ids"] = ",".join(category_ids)

        headers = self._headers()
        if buyer_postal_code:
            headers["X-EBAY-C-ENDUSERCTX"] = (
                f"contextualLocation=country=US,zip={buyer_postal_code}"
            )

        return self._request("GET", url, params=params, headers=headers)

    def get_item(self, item_id: str) -> dict[str, Any]:
        """Get full item details by eBay item ID."""
        url = f"{self._base_url}/item/{item_id}"
        return self._request("GET", url, headers=self._headers())

    def get_items_by_group(self, item_group_id: str) -> dict[str, Any]:
        """Get all items in a product group (variations)."""
        url = f"{self._base_url}/item/get_items_by_item_group"
        params = {"item_group_id": item_group_id}
        return self._request("GET", url, params=params, headers=self._headers())

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw eBay listing data."""
        keyword = kwargs.get("keyword", "")
        if not keyword:
            return []

        result = self.search(
            keyword,
            category_ids=kwargs.get("category_ids"),
            filter_conditions=kwargs.get("conditions"),
            price_min=kwargs.get("price_min"),
            price_max=kwargs.get("price_max"),
            sort=kwargs.get("sort", "price"),
            limit=kwargs.get("limit", 50),
            buyer_postal_code=kwargs.get("postal_code"),
        )

        return result.get("itemSummaries", [])

    def close(self) -> None:
        super().close()
        self._auth.close()
