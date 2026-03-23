"""Best Buy Products API adapter."""

from __future__ import annotations

import logging
from typing import Any, Optional

from techwatch.adapters.base import BaseAdapter
from techwatch.config import get_settings

logger = logging.getLogger(__name__)

BESTBUY_API_BASE = "https://api.bestbuy.com/v1"


class BestBuyProductsAdapter(BaseAdapter):
    """Fetch product data from the Best Buy Products API."""

    source_name = "bestbuy_products"
    max_qps = 5.0
    burst = 5
    cache_ttl = 300

    def __init__(self) -> None:
        super().__init__()
        settings = get_settings()
        self._api_key = settings.bestbuy_api_key.get_secret_value()

    def _build_url(self, endpoint: str) -> str:
        return f"{BESTBUY_API_BASE}/{endpoint}"

    def search(
        self,
        keyword: str,
        *,
        category_id: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        """Search products by keyword and optional filters.

        Returns the raw Best Buy API response.
        """
        # Build filter string
        filters = [f'search={keyword}']
        if category_id:
            filters.append(f'categoryPath.id={category_id}')
        if min_price is not None:
            filters.append(f'salePrice>={min_price}')
        if max_price is not None:
            filters.append(f'salePrice<={max_price}')

        filter_str = "&".join(filters) if len(filters) > 1 else filters[0]
        url = self._build_url(f"products({filter_str})")

        params = {
            "apiKey": self._api_key,
            "format": "json",
            "show": (
                "sku,name,brandName,modelNumber,upc,categoryPath,salePrice,"
                "regularPrice,onSale,savings,savingsAsPercentageOfRegularPrice,"
                "priceUpdateDate,freeShipping,shippingCost,details,"
                "condition,image,url,addToCartUrl,customerReviewAverage,"
                "customerReviewCount,inStoreAvailability,onlineAvailability,"
                "shortDescription,longDescription"
            ),
            "pageSize": page_size,
            "page": page,
        }

        return self._request("GET", url, params=params)

    def get_by_sku(self, sku: int) -> dict[str, Any]:
        """Fetch a single product by SKU."""
        url = self._build_url(f"products/{sku}.json")
        params = {"apiKey": self._api_key, "format": "json"}
        return self._request("GET", url, params=params)

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw product data."""
        keyword = kwargs.get("keyword", "")
        if not keyword:
            return []

        result = self.search(
            keyword,
            category_id=kwargs.get("category_id"),
            min_price=kwargs.get("min_price"),
            max_price=kwargs.get("max_price"),
            page=kwargs.get("page", 1),
            page_size=kwargs.get("page_size", 25),
        )

        return result.get("products", [])
