"""Normalization engine — maps raw adapter output to canonical domain model.

This module is DETERMINISTIC PYTHON ONLY — no LLM calls.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from techwatch.models import Offer, Pricing, Product, Specs
from techwatch.models.enums import CanonicalCondition, SellerType, Source
from techwatch.models.offer import Condition, Delivery, Merchant
from techwatch.normalization.condition import (
    normalize_bestbuy_condition,
    normalize_ebay_condition,
)

logger = logging.getLogger(__name__)

_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "laptop": ["laptop", "notebook", "ultrabook", "chromebook", "macbook"],
    "monitor": ["monitor", "display", "screen"],
    "headphones": ["headphone", "earphone", "earbud"],  # Must be before 'phone'
    "phone": ["smartphone", "iphone", "galaxy", " phone"],  # Leading space avoids 'headphone'
    "tablet": ["tablet", "ipad"],
    "keyboard": ["keyboard"],
    "gpu": ["graphics", "gpu", "video card"],
    "tv": ["television", "tv", "oled", "qled"],
    "desktop": ["desktop", "pc", "tower", "imac"],
}


def _parse_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        cleaned = str(value).split()[0].replace(",", "").replace("GB", "").replace("gb", "")
        return int(float(cleaned))
    except (ValueError, TypeError, IndexError):
        return None


def _parse_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).replace(",", "").replace("$", ""))
    except (ValueError, TypeError):
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _infer_category(category_path: list[str]) -> str:
    path_lower = " ".join(category_path).lower()
    for canonical, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in path_lower for kw in keywords):
            return canonical
    return category_path[-1].lower() if category_path else "other"


def normalize_bestbuy_product(raw: dict[str, Any]) -> tuple[Product, Offer]:
    """Normalize a raw Best Buy product."""
    sku = str(raw.get("sku", ""))
    cat_path = [c.get("name", "") for c in raw.get("categoryPath", [])]

    specs_dict: dict[str, Any] = {}
    for d in raw.get("details", []):
        name = d.get("name", "").lower().replace(" ", "_")
        if name:
            specs_dict[name] = d.get("value", "")

    specs = Specs(
        cpu=specs_dict.get("processor_model") or specs_dict.get("processor"),
        ram_gb=_parse_int(specs_dict.get("system_memory_ram")),
        storage_gb=_parse_int(specs_dict.get("total_storage_capacity")),
        screen_in=_parse_float(specs_dict.get("screen_size")),
        gpu=specs_dict.get("gpu_brand"),
    )

    product = Product(
        canonical_product_id=f"bestbuy:bestbuy:{sku}",
        title=raw.get("name", ""),
        brand=raw.get("brandName"),
        model=raw.get("modelNumber"),
        upc_gtin=raw.get("upc"),
        canonical_category=_infer_category(cat_path),
        source_category_path=cat_path,
        specs=specs,
        images=[raw["image"]] if raw.get("image") else [],
        url=raw.get("url"),
    )

    pricing = Pricing(
        list_amount=raw.get("regularPrice"),
        sale_amount=raw.get("salePrice"),
        currency="USD",
        shipping_amount=0.0 if raw.get("freeShipping") else (raw.get("shippingCost") or 0.0),
        price_updated_at=_parse_datetime(raw.get("priceUpdateDate")),
    )

    condition = normalize_bestbuy_condition(raw.get("condition", "New"))

    offer = Offer(
        offer_id=f"bb-{sku}",
        source=Source.BESTBUY,
        condition=condition,
        pricing=pricing,
        delivery=Delivery(pickup_available=raw.get("inStoreAvailability", False)),
        merchant=Merchant(
            seller_name="Best Buy", marketplace="Best Buy",
            seller_type=SellerType.RETAILER,
        ),
        url=raw.get("url"),
    )
    return product, offer


def normalize_ebay_item(raw: dict[str, Any]) -> tuple[Product, Offer]:
    """Normalize a raw eBay item summary."""
    item_id = raw.get("itemId", "")
    cat_path = [c.get("categoryName", "") for c in raw.get("categories", [])]

    product = Product(
        canonical_product_id=f"ebay:ebay:{item_id}",
        title=raw.get("title", ""),
        brand=raw.get("brand"),
        canonical_category=_infer_category(cat_path),
        source_category_path=cat_path,
        url=raw.get("itemWebUrl"),
    )

    price_data = raw.get("price", {})
    ship_opts = raw.get("shippingOptions", [{}])
    ship_cost = ship_opts[0].get("shippingCost", {}) if ship_opts else {}

    pricing = Pricing(
        sale_amount=_parse_float(price_data.get("value")),
        currency=price_data.get("currency", "USD"),
        shipping_amount=_parse_float(ship_cost.get("value")) or 0.0,
    )

    cond_id = raw.get("conditionId")
    condition = (
        normalize_ebay_condition(int(cond_id), raw.get("condition", ""))
        if cond_id else Condition(canonical=CanonicalCondition.UNKNOWN)
    )

    seller = raw.get("seller", {})
    offer = Offer(
        offer_id=f"ebay-{item_id}",
        source=Source.EBAY,
        condition=condition,
        pricing=pricing,
        merchant=Merchant(
            seller_name=seller.get("username"),
            marketplace="eBay",
            seller_type=SellerType.MARKETPLACE_SELLER,
            seller_feedback_pct=_parse_float(seller.get("feedbackPercentage")),
            seller_feedback_count=_parse_int(seller.get("feedbackScore")),
        ),
        url=raw.get("itemWebUrl"),
    )
    return product, offer


def normalize_jsonld_product(raw: dict[str, Any]) -> list[tuple[Product, Offer]]:
    """Normalize a structured data extraction result."""
    results: list[tuple[Product, Offer]] = []

    text_lower = (raw.get("category") or raw.get("name", "")).lower()
    category = "other"
    for canonical, keywords in _CATEGORY_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            category = canonical
            break

    product = Product(
        canonical_product_id=f"web:structured:{raw.get('sku', 'unknown')}",
        title=raw.get("name", ""),
        brand=raw.get("brand", ""),
        model=raw.get("model", ""),
        upc_gtin=raw.get("gtin") or None,
        canonical_category=category,
        url=raw.get("url"),
    )

    for i, offer_raw in enumerate(raw.get("offers", [])):
        pricing = Pricing(
            sale_amount=offer_raw.get("price"),
            currency=offer_raw.get("currency", "USD"),
            shipping_amount=_parse_float(
                offer_raw.get("shipping", {}).get("cost")
            ) or 0.0,
        )
        seller = offer_raw.get("seller", {})
        offer = Offer(
            offer_id=f"web-{raw.get('sku', 'unknown')}-{i}",
            source=Source.STRUCTURED_WEB,
            condition=Condition(canonical=CanonicalCondition.UNKNOWN),
            pricing=pricing,
            merchant=Merchant(
                seller_name=seller.get("name") or None,
                marketplace=seller.get("name", "Web"),
                seller_type=SellerType.RETAILER
                if seller.get("type") == "Organization"
                else SellerType.UNKNOWN,
            ),
            url=offer_raw.get("url"),
        )
        results.append((product, offer))
    return results
