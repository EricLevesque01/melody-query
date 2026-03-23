"""eBay Taxonomy API adapter."""

from __future__ import annotations

import logging
from typing import Any

from techwatch.adapters.base import BaseAdapter
from techwatch.adapters.ebay.auth import EbayAuth

logger = logging.getLogger(__name__)

EBAY_TAXONOMY_BASE = "https://api.ebay.com/commerce/taxonomy/v1"


class EbayTaxonomyAdapter(BaseAdapter):
    """Navigate the eBay category taxonomy."""

    source_name = "ebay_taxonomy"
    max_qps = 5.0
    burst = 10
    cache_ttl = 86400  # Taxonomy changes very infrequently

    def __init__(self, sandbox: bool = False) -> None:
        super().__init__()
        self._auth = EbayAuth(sandbox=sandbox)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._auth.get_token()}"}

    def get_default_category_tree_id(
        self, marketplace_id: str = "EBAY_US"
    ) -> str:
        """Get the default category tree ID for a marketplace."""
        url = f"{EBAY_TAXONOMY_BASE}/get_default_category_tree_id"
        params = {"marketplace_id": marketplace_id}
        result = self._request("GET", url, params=params, headers=self._headers())
        return result.get("categoryTreeId", "0")

    def get_category_tree(self, tree_id: str = "0") -> dict[str, Any]:
        """Get the full category tree."""
        url = f"{EBAY_TAXONOMY_BASE}/category_tree/{tree_id}"
        return self._request("GET", url, headers=self._headers())

    def get_category_subtree(
        self, tree_id: str, category_id: str
    ) -> dict[str, Any]:
        """Get a subtree starting from a specific category."""
        url = f"{EBAY_TAXONOMY_BASE}/category_tree/{tree_id}/get_category_subtree"
        params = {"category_id": category_id}
        return self._request("GET", url, params=params, headers=self._headers())

    def get_category_suggestions(
        self, tree_id: str, query: str
    ) -> list[dict[str, Any]]:
        """Get category suggestions for a search query."""
        url = f"{EBAY_TAXONOMY_BASE}/category_tree/{tree_id}/get_category_suggestions"
        params = {"q": query}
        result = self._request("GET", url, params=params, headers=self._headers())
        return result.get("categorySuggestions", [])

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw taxonomy data."""
        tree_id = kwargs.get("tree_id", "0")
        category_id = kwargs.get("category_id")
        query = kwargs.get("query")

        if query:
            return self.get_category_suggestions(tree_id, query)
        elif category_id:
            subtree = self.get_category_subtree(tree_id, category_id)
            return [subtree]
        else:
            tree = self.get_category_tree(tree_id)
            return [tree]

    def close(self) -> None:
        super().close()
        self._auth.close()
