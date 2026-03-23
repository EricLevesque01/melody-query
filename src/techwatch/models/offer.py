"""Offer domain model — a specific listing for a product."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from techwatch.models.enums import (
    CanonicalCondition,
    CosmeticGrade,
    FunctionalState,
    SellerType,
    Source,
)


class Condition(BaseModel):
    """Three-axis condition representation.

    ``canonical`` is the vendor-neutral label used for filtering / scoring.
    ``source_label`` preserves the exact text from the marketplace.
    ``functional_state`` and ``cosmetic_grade`` capture the two independent
    dimensions that differ across Back Market, Swappa, eBay, and Best Buy.
    """

    model_config = ConfigDict(strict=True)

    canonical: CanonicalCondition = CanonicalCondition.UNKNOWN
    source_label: Optional[str] = None
    functional_state: FunctionalState = FunctionalState.UNKNOWN
    cosmetic_grade: CosmeticGrade = CosmeticGrade.UNKNOWN


class Pricing(BaseModel):
    """Price snapshot with original and converted amounts."""

    model_config = ConfigDict(strict=True)

    list_amount: Optional[float] = None
    sale_amount: Optional[float] = None
    currency: str = "USD"
    converted_amount: Optional[float] = None
    converted_currency: Optional[str] = None
    shipping_amount: float = 0.0
    known_tax_included: bool = False
    price_updated_at: Optional[datetime] = None

    @property
    def effective_price(self) -> float:
        """Return the best available item price."""
        return self.sale_amount or self.list_amount or 0.0

    @property
    def total_landed_cost(self) -> float:
        """Item price + shipping (excludes unknown tax)."""
        return self.effective_price + self.shipping_amount


class Delivery(BaseModel):
    """Shipping / delivery information."""

    model_config = ConfigDict(strict=True)

    service_level: Optional[str] = None
    earliest_delivery_at: Optional[datetime] = None
    latest_delivery_at: Optional[datetime] = None
    pickup_available: bool = False


class Merchant(BaseModel):
    """Seller / marketplace metadata."""

    model_config = ConfigDict(strict=True)

    seller_name: Optional[str] = None
    marketplace: str
    seller_type: SellerType = SellerType.UNKNOWN
    seller_feedback_pct: Optional[float] = None
    seller_feedback_count: Optional[int] = None


class Offer(BaseModel):
    """A concrete listing that ties a product to a price, condition, and seller."""

    model_config = ConfigDict(strict=True)

    offer_id: str
    source: Source
    condition: Condition = Condition()
    pricing: Pricing
    delivery: Delivery = Delivery()
    merchant: Merchant
    url: Optional[str] = None
    observed_at: datetime = datetime.utcnow()  # noqa: DTZ003
    raw_source_ref: Optional[dict[str, Any]] = None
