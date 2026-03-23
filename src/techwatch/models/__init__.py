"""Domain models package — canonical schemas for the TechWatch pipeline."""

from techwatch.models.analysis import Analysis, ScoreComponents
from techwatch.models.enums import (
    CanonicalCondition,
    CosmeticGrade,
    FunctionalState,
    SellerType,
    Source,
    TriggerMetric,
    TriggerOperator,
    WatchStatus,
)
from techwatch.models.narrative import DigestEntry, DigestPayload, OfferNarrative
from techwatch.models.offer import Condition, Delivery, Merchant, Offer, Pricing
from techwatch.models.product import Product, Specs
from techwatch.models.search import SearchPlan, SearchQuery, SearchResponse, SearchResult
from techwatch.models.watch import AlertDecision, Watch, WatchTrigger

__all__ = [
    # enums
    "CanonicalCondition",
    "CosmeticGrade",
    "FunctionalState",
    "SellerType",
    "Source",
    "TriggerMetric",
    "TriggerOperator",
    "WatchStatus",
    # product
    "Product",
    "Specs",
    # offer
    "Condition",
    "Delivery",
    "Merchant",
    "Offer",
    "Pricing",
    # analysis
    "Analysis",
    "ScoreComponents",
    # search
    "SearchPlan",
    "SearchQuery",
    "SearchResponse",
    "SearchResult",
    # watch
    "AlertDecision",
    "Watch",
    "WatchTrigger",
    # narrative
    "DigestEntry",
    "DigestPayload",
    "OfferNarrative",
]
