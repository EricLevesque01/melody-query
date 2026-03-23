"""Structured data (JSON-LD) extractor for Schema.org Product/Offer markup."""

from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import httpx

from techwatch.adapters.base import BaseAdapter

logger = logging.getLogger(__name__)


class JsonLdExtractor(BaseAdapter):
    """Extract Schema.org Product and Offer data from web pages via JSON-LD.

    Priority order: JSON-LD > microdata fallback (future).
    This adapter does NOT use the domain allowlist since it fetches
    arbitrary product pages. Instead it validates output structure.
    """

    source_name = "structured_web"
    max_qps = 2.0
    burst = 3
    cache_ttl = 600

    def _fetch_page(self, url: str) -> str:
        """Fetch raw HTML from a product page URL."""
        self._rate_limiter.acquire()
        response = self._client.get(url)
        response.raise_for_status()
        return response.text

    def _extract_jsonld_blocks(self, html: str) -> list[dict[str, Any]]:
        """Extract all JSON-LD script blocks from HTML."""
        pattern = r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>'
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)

        blocks: list[dict[str, Any]] = []
        for match in matches:
            try:
                data = json.loads(match.strip())
                if isinstance(data, list):
                    blocks.extend(data)
                else:
                    blocks.append(data)
            except json.JSONDecodeError:
                logger.debug("Failed to parse JSON-LD block")
                continue
        return blocks

    def _find_products(
        self, blocks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Find Product entities in JSON-LD blocks (including @graph)."""
        products: list[dict[str, Any]] = []
        for block in blocks:
            if block.get("@type") == "Product":
                products.append(block)
            elif "@graph" in block:
                for item in block["@graph"]:
                    if isinstance(item, dict) and item.get("@type") == "Product":
                        products.append(item)
        return products

    def _normalize_product(
        self, product: dict[str, Any], source_url: str
    ) -> dict[str, Any]:
        """Normalize a Schema.org Product into a flat intermediate dict."""
        offers_raw = product.get("offers", {})
        if isinstance(offers_raw, list):
            offers = offers_raw
        elif isinstance(offers_raw, dict):
            if offers_raw.get("@type") == "AggregateOffer":
                offers = offers_raw.get("offers", [offers_raw])
                if isinstance(offers, dict):
                    offers = [offers]
            else:
                offers = [offers_raw]
        else:
            offers = []

        normalized_offers = []
        for offer in offers:
            if not isinstance(offer, dict):
                continue
            normalized_offers.append({
                "price": self._parse_price(offer.get("price")),
                "currency": offer.get("priceCurrency", "USD"),
                "availability": offer.get("availability", ""),
                "condition": offer.get("itemCondition", ""),
                "seller": self._extract_seller(offer),
                "url": offer.get("url", source_url),
                "shipping": self._extract_shipping(offer),
            })

        return {
            "name": product.get("name", ""),
            "brand": self._extract_brand(product),
            "model": product.get("model", product.get("mpn", "")),
            "gtin": (
                product.get("gtin13")
                or product.get("gtin14")
                or product.get("gtin12")
                or product.get("gtin")
                or product.get("isbn")
                or ""
            ),
            "sku": product.get("sku", ""),
            "description": product.get("description", ""),
            "image": self._extract_image(product),
            "category": product.get("category", ""),
            "url": source_url,
            "offers": normalized_offers,
            "raw": product,
        }

    @staticmethod
    def _parse_price(price: Any) -> Optional[float]:
        if price is None:
            return None
        try:
            return float(str(price).replace(",", ""))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_brand(product: dict[str, Any]) -> str:
        brand = product.get("brand", "")
        if isinstance(brand, dict):
            return brand.get("name", "")
        return str(brand)

    @staticmethod
    def _extract_image(product: dict[str, Any]) -> str:
        image = product.get("image", "")
        if isinstance(image, list):
            return image[0] if image else ""
        if isinstance(image, dict):
            return image.get("url", "")
        return str(image)

    @staticmethod
    def _extract_seller(offer: dict[str, Any]) -> dict[str, str]:
        seller = offer.get("seller", {})
        if isinstance(seller, dict):
            return {
                "name": seller.get("name", ""),
                "type": seller.get("@type", ""),
            }
        return {"name": "", "type": ""}

    @staticmethod
    def _extract_shipping(offer: dict[str, Any]) -> dict[str, Any]:
        shipping = offer.get("shippingDetails", offer.get("shipping", {}))
        if isinstance(shipping, dict):
            rate = shipping.get("shippingRate", {})
            return {
                "cost": rate.get("value") if isinstance(rate, dict) else None,
                "currency": rate.get("currency", "USD") if isinstance(rate, dict) else "USD",
            }
        return {"cost": None, "currency": "USD"}

    def extract_from_url(self, url: str) -> list[dict[str, Any]]:
        """Extract all Product entities from a URL."""
        html = self._fetch_page(url)
        blocks = self._extract_jsonld_blocks(html)
        products = self._find_products(blocks)
        return [self._normalize_product(p, url) for p in products]

    def fetch_raw(self, **kwargs: Any) -> list[dict[str, Any]]:
        """Fetch raw structured data from a URL."""
        url = kwargs.get("url", "")
        if not url:
            return []
        return self.extract_from_url(url)
