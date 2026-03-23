"""Best Buy Categories API adapter."""

from __future__ import annotations

import logging
from typing import Any

from techwatch.adapters.base import BaseAdapter
from techwatch.config import get_settings

logger = logging.getLogger(__name__)

BESTBUY_API_BASE = "https://api.bestbuy.com/v1"


class BestBuyCategoriesAdapter(BaseAdapter):
    """Fetch category taxonomy from the Best Buy Categories API."""

    source_name = "bestbuy_categories"
    max_qps = 5.0
    burst = 5
    cache_ttl = 3600  # Categories change infrequently

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.bestbuy_api_key.get_secret_value()

    def get_top_level(self) -> list[dict[str, Any]]:
        """Get top-level categories."""
        url = f"{BESTBUY_API_BASE}/categories"
        params = {
            "apiKey": self._api_key,
            "format": "json",
            "show": "id,name,url,path,subCategories.id,subCategories.name",
            "pageSize": 100,
        }
        result = self._request("GET", url, params=params)
        return result.get("categories", [])

    def get_by_id(self, category_id: str) -> dict[str, Any]:
        """Get a specific category and its subcategories."""
        url = f"{BESTBUY_API_BASE}/categories(id={category_id})"
        params = {
            "apiKey": self._api_key,
            "format": "json",
            "show": "id,name,url,path,subCategories.id,subCategories.name",
        }
        result = self._request("GET", url, params=params)
        categories = result.get("categories", [])
        return categories[0] if categories else {}

    def search_categories(self, name: str) -> list[dict[str, Any]]:
        """Search categories by name."""
        url = f"{BESTBUY_API_BASE}/categories(name={name}*)"
        params = {
            "apiKey": self._api_key,
            "format": "json",
            "show": "id,name,url,path",
            "pageSize": 20,
        }
        result = self._request("GET", url, params=params)
        return result.get("categories", [])

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw category data."""
        category_id = kwargs.get("category_id")
        name = kwargs.get("name")

        if category_id:
            cat = self.get_by_id(category_id)
            return [cat] if cat else []
        elif name:
            return self.search_categories(name)
        else:
            return self.get_top_level()
