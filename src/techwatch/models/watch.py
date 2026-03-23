"""Watch and alert models — saved searches and trigger logic."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from techwatch.models.enums import (
    CanonicalCondition,
    TriggerMetric,
    TriggerOperator,
    WatchStatus,
)


class WatchTrigger(BaseModel):
    """A single alert condition, e.g. ``price_drop_pct >= 8``."""

    model_config = ConfigDict(strict=True)

    metric: TriggerMetric
    operator: TriggerOperator
    threshold: float


class Watch(BaseModel):
    """A persisted saved search with schedule and alert configuration."""

    model_config = ConfigDict(strict=True)

    watch_id: str = Field(default_factory=lambda: uuid4().hex[:12])
    raw_query: str
    budget: Optional[float] = None
    country: str = "US"
    postal_code: Optional[str] = None
    currency: str = "USD"
    conditions: list[CanonicalCondition] = Field(
        default_factory=lambda: list(CanonicalCondition)
    )
    top_n: int = 10
    schedule: str = "0 9 * * *"  # cron expression
    timezone: str = "America/New_York"
    email: Optional[str] = None
    triggers: list[WatchTrigger] = []
    status: WatchStatus = WatchStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_run_at: Optional[datetime] = None
    next_run_at: Optional[datetime] = None

    # Subscription / compliance fields
    subscription_status: str = "subscribed"
    digest_frequency: str = "per_trigger"
    last_opt_out_at: Optional[datetime] = None


class AlertDecision(BaseModel):
    """Structured output from the Deal Analyst.

    Describes *whether* an alert should fire and *why*.
    """

    model_config = ConfigDict(strict=True)

    should_alert: bool = False
    triggered_rules: list[str] = []
    headline: str = ""
    summary: str = ""
    top_offer_ids: list[str] = []
