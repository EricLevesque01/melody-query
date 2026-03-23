"""Mock adapter implementations for demo/development mode.

These adapters implement the same interface as real adapters but return
realistic fixture data without making any network calls. Activated by
setting ``TECHWATCH_MOCK=true`` in the environment.
"""

from __future__ import annotations

import logging
from typing import Any

from techwatch.adapters.mock.fixtures import (
    get_mock_bestbuy_openbox,
    get_mock_bestbuy_products,
    get_mock_ebay_items,
)

logger = logging.getLogger(__name__)


class MockBestBuyProductsAdapter:
    """Mock Best Buy Products API adapter."""

    source_name = "bestbuy_products"

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Return mock product data."""
        keyword = kwargs.get("keyword", "")
        logger.info("[MOCK] BestBuy Products search: '%s'", keyword)
        return get_mock_bestbuy_products(keyword, **kwargs)

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class MockBestBuyOpenBoxAdapter:
    """Mock Best Buy Open Box API adapter."""

    source_name = "bestbuy_openbox"

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Return mock open box data."""
        keyword = kwargs.get("keyword", "")
        logger.info("[MOCK] BestBuy Open Box search: '%s'", keyword)
        return get_mock_bestbuy_openbox(keyword, **kwargs)

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class MockEbayBrowseAdapter:
    """Mock eBay Browse API adapter."""

    source_name = "ebay_browse"

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Return mock eBay item data."""
        keyword = kwargs.get("keyword", "")
        logger.info("[MOCK] eBay Browse search: '%s'", keyword)
        return get_mock_ebay_items(keyword, **kwargs)

    def close(self) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
