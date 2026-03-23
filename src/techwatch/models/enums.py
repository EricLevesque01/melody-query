"""Canonical enumerations for the TechWatch domain model.

These enums provide vendor-neutral labels while keeping source-specific
truth available through companion free-text fields on the parent models.
"""

from __future__ import annotations

from enum import Enum


# ── Condition ───────────────────────────────────────────────────────


class CanonicalCondition(str, Enum):
    """Vendor-neutral item condition."""

    NEW = "new"
    OPEN_BOX = "open_box"
    CERTIFIED_REFURBISHED = "certified_refurbished"
    REFURBISHED = "refurbished"
    USED_LIKE_NEW = "used_like_new"
    USED_GOOD = "used_good"
    USED_FAIR = "used_fair"
    FOR_PARTS = "for_parts"
    UNKNOWN = "unknown"


class FunctionalState(str, Enum):
    """Whether the device is confirmed to work correctly."""

    FULLY_FUNCTIONAL = "fully_functional"
    MINOR_ISSUES = "minor_issues"
    MAJOR_ISSUES = "major_issues"
    FOR_PARTS = "for_parts"
    UNKNOWN = "unknown"


class CosmeticGrade(str, Enum):
    """Visual / physical appearance grade."""

    PRISTINE = "pristine"
    PREMIUM = "premium"
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    UNKNOWN = "unknown"


# ── Source & Merchant ───────────────────────────────────────────────


class Source(str, Enum):
    """Data source / adapter that produced the record."""

    BESTBUY = "bestbuy"
    EBAY = "ebay"
    STRUCTURED_WEB = "structured_web"
    MANUAL = "manual"


class SellerType(str, Enum):
    """Nature of the selling entity."""

    RETAILER = "retailer"
    MARKETPLACE_SELLER = "marketplace_seller"
    UNKNOWN = "unknown"


# ── Search & Watch ──────────────────────────────────────────────────


class WatchStatus(str, Enum):
    """Lifecycle state of a saved watch."""

    ACTIVE = "active"
    PAUSED = "paused"
    DELETED = "deleted"


class TriggerOperator(str, Enum):
    """Comparison operators supported in alert triggers."""

    GTE = ">="
    LTE = "<="
    GT = ">"
    LT = "<"
    EQ = "=="


class TriggerMetric(str, Enum):
    """Metrics that can fire an alert."""

    PRICE_DROP_PCT = "price_drop_pct"
    PRICE_BELOW = "price_below"
    NEW_OFFER_RANK = "new_offer_rank"
    AVAILABILITY_CHANGE = "availability_change"
    CONDITION_UPGRADE = "condition_upgrade"
