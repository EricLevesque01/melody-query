"""Taxonomy module — map between retailer-specific and canonical categories.

This is deterministic Python only — no LLM calls.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategoryMapping:
    """A mapping from retailer-specific category to canonical category."""

    source: str
    source_category_id: str
    source_category_name: str
    canonical_category: str


# ── Best Buy Category Mappings ──────────────────────────────────────

BESTBUY_CATEGORY_MAP: dict[str, str] = {
    # Top-level
    "abcat0502000": "laptop",
    "pcmcat138500050001": "laptop",
    "pcmcat247400050000": "laptop",
    "pcmcat209000050006": "desktop",
    "abcat0101000": "tv",
    "pcmcat241600050001": "monitor",
    "pcmcat209400050001": "tablet",
    "abcat0800000": "phone",
    "abcat0204000": "headphones",
    "pcmcat241000050007": "keyboard",
    "abcat0513000": "gpu",
    "abcat0507000": "cpu",
    "pcmcat158500050004": "ssd",
    "pcmcat370800050045": "camera",
}


def resolve_bestbuy_category(category_id: str) -> str:
    """Map a Best Buy category ID to a canonical category."""
    return BESTBUY_CATEGORY_MAP.get(category_id, "other")


# ── eBay Category Mappings ──────────────────────────────────────────

EBAY_CATEGORY_MAP: dict[str, str] = {
    "175672": "laptop",
    "111422": "laptop",
    "179": "desktop",
    "1249": "monitor",
    "171485": "tablet",
    "9355": "phone",
    "112529": "headphones",
    "33963": "keyboard",
    "27386": "gpu",
    "164": "cpu",
    "175669": "ssd",
    "31388": "camera",
    "11071": "tv",
}


def resolve_ebay_category(category_id: str) -> str:
    """Map an eBay category ID to a canonical category."""
    return EBAY_CATEGORY_MAP.get(str(category_id), "other")


# ── Canonical Category Registry ────────────────────────────────────

CANONICAL_CATEGORIES: dict[str, dict[str, str]] = {
    "laptop": {"label": "Laptops & Notebooks", "icon": "laptop"},
    "desktop": {"label": "Desktop Computers", "icon": "computer"},
    "monitor": {"label": "Monitors & Displays", "icon": "monitor"},
    "tablet": {"label": "Tablets", "icon": "tablet"},
    "phone": {"label": "Smartphones", "icon": "phone"},
    "headphones": {"label": "Headphones & Earbuds", "icon": "headphones"},
    "keyboard": {"label": "Keyboards", "icon": "keyboard"},
    "mouse": {"label": "Mice & Trackpads", "icon": "mouse"},
    "gpu": {"label": "Graphics Cards", "icon": "gpu"},
    "cpu": {"label": "Processors", "icon": "cpu"},
    "ssd": {"label": "Solid State Drives", "icon": "storage"},
    "ram": {"label": "Memory (RAM)", "icon": "memory"},
    "camera": {"label": "Cameras", "icon": "camera"},
    "tv": {"label": "Televisions", "icon": "tv"},
    "other": {"label": "Other", "icon": "device"},
}


def get_category_label(canonical_category: str) -> str:
    """Return a human-readable label for a canonical category."""
    info = CANONICAL_CATEGORIES.get(canonical_category)
    return info["label"] if info else canonical_category.title()


def get_all_categories() -> list[str]:
    """Return all canonical category keys."""
    return list(CANONICAL_CATEGORIES.keys())
