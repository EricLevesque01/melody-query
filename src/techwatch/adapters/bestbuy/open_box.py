"""Best Buy Open Box API adapter."""

from __future__ import annotations

import logging
from typing import Any

from techwatch.adapters.base import BaseAdapter
from techwatch.config import get_settings

logger = logging.getLogger(__name__)

BESTBUY_API_BASE = "https://api.bestbuy.com/beta"


class BestBuyOpenBoxAdapter(BaseAdapter):
    """Fetch open-box offers from the Best Buy Open Box API."""

    source_name = "bestbuy_openbox"
    max_qps = 3.0
    burst = 3
    cache_ttl = 180  # Open box inventory changes faster

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.bestbuy_api_key.get_secret_value()

    def get_by_sku(self, sku: int) -> list[dict[str, Any]]:
        """Get open-box offers for a specific SKU."""
        url = f"{BESTBUY_API_BASE}/products/{sku}/openBox"
        params = {"apiKey": self._api_key, "format": "json"}
        result = self._request("GET", url, params=params)
        return result.get("results", [])

    def get_by_category(
        self,
        category_id: str,
        *,
        page: int = 1,
        page_size: int = 25,
    ) -> list[dict[str, Any]]:
        """Get open-box offers for an entire category."""
        url = f"{BESTBUY_API_BASE}/products/openBox(categoryId={category_id})"
        params = {
            "apiKey": self._api_key,
            "format": "json",
            "pageSize": page_size,
            "page": page,
        }
        result = self._request("GET", url, params=params)
        return result.get("results", [])

    def get_all(
        self,
        *,
        page: int = 1,
        page_size: int = 25,
    ) -> list[dict[str, Any]]:
        """Get all available open-box offers."""
        url = f"{BESTBUY_API_BASE}/products/openBox"
        params = {
            "apiKey": self._api_key,
            "format": "json",
            "pageSize": page_size,
            "page": page,
        }
        result = self._request("GET", url, params=params)
        return result.get("results", [])

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw open-box offer data."""
        sku = kwargs.get("sku")
        category_id = kwargs.get("category_id")

        if sku:
            return self.get_by_sku(int(sku))
        elif category_id:
            return self.get_by_category(
                category_id,
                page=kwargs.get("page", 1),
                page_size=kwargs.get("page_size", 25),
            )
        else:
            return self.get_all(
                page=kwargs.get("page", 1),
                page_size=kwargs.get("page_size", 25),
            )
