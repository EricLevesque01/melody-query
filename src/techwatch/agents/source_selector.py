"""Source selector — chooses which adapters to query based on the search plan.

This is deterministic logic, not an LLM call.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from techwatch.models import SearchPlan
from techwatch.models.enums import CanonicalCondition, Source

logger = logging.getLogger(__name__)


@dataclass
class AdapterSelection:
    """A chosen adapter with its query configuration."""

    source: Source
    adapter_name: str
    query_params: dict[str, Any]
    priority: int  # Lower = higher priority


def select_sources(plan: SearchPlan) -> list[AdapterSelection]:
    """Choose adapters and ordering based on the search plan.

    Rules:
    - Best Buy for US new/open-box/certified queries
    - eBay for all condition types, especially used/refurbished
    - Structured web only when explicit URLs provided
    - Skip sources that don't support the requested conditions
    """
    selections: list[AdapterSelection] = []

    has_new = CanonicalCondition.NEW in plan.conditions
    has_open_box = CanonicalCondition.OPEN_BOX in plan.conditions
    has_certified = CanonicalCondition.CERTIFIED_REFURBISHED in plan.conditions
    has_refurb = CanonicalCondition.REFURBISHED in plan.conditions
    has_used = any(
        c in plan.conditions
        for c in (
            CanonicalCondition.USED_LIKE_NEW,
            CanonicalCondition.USED_GOOD,
            CanonicalCondition.USED_FAIR,
        )
    )

    is_us = plan.country.upper() == "US"

    # Best Buy Products — US new items
    if is_us and has_new:
        selections.append(
            AdapterSelection(
                source=Source.BESTBUY,
                adapter_name="bestbuy_products",
                query_params={
                    "keyword": " ".join(plan.keywords) or plan.canonical_category,
                    "max_price": plan.budget_max,
                },
                priority=1 if Source.BESTBUY in plan.preferred_sources else 2,
            )
        )

    # Best Buy Open Box — US open-box/certified
    if is_us and (has_open_box or has_certified):
        selections.append(
            AdapterSelection(
                source=Source.BESTBUY,
                adapter_name="bestbuy_openbox",
                query_params={
                    "keyword": " ".join(plan.keywords) or plan.canonical_category,
                },
                priority=2,
            )
        )

    # eBay Browse — all conditions, especially used/refurbished
    ebay_conditions = []
    if has_new:
        ebay_conditions.append("NEW")
    if has_open_box:
        ebay_conditions.append("NEW_OTHER")
    if has_certified:
        ebay_conditions.append("CERTIFIED_REFURBISHED")
    if has_refurb:
        ebay_conditions.extend(["SELLER_REFURBISHED", "REFURBISHED"])
    if has_used:
        ebay_conditions.append("USED")

    if ebay_conditions or not selections:
        selections.append(
            AdapterSelection(
                source=Source.EBAY,
                adapter_name="ebay_browse",
                query_params={
                    "keyword": " ".join(plan.keywords) or plan.canonical_category,
                    "conditions": ebay_conditions or None,
                    "price_max": plan.budget_max,
                    "postal_code": plan.postal_code,
                },
                priority=1 if Source.EBAY in plan.preferred_sources else 3,
            )
        )

    # Sort by priority
    selections.sort(key=lambda s: s.priority)

    logger.info(
        "Source selector: %d adapters chosen: %s",
        len(selections),
        [s.adapter_name for s in selections],
    )
    return selections
