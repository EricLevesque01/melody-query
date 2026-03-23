"""Repository pattern for database CRUD operations."""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from techwatch.models import (
    Analysis,
    Offer,
    Product,
    ScoreComponents,
    SearchResult,
    Watch,
    WatchTrigger,
)
from techwatch.models.enums import CanonicalCondition, WatchStatus
from techwatch.persistence.tables import (
    OfferRow,
    PriceHistoryRow,
    WatchRow,
    WatchRunRow,
)


# ── Offer Repository ───────────────────────────────────────────────


class OfferRepo:
    """Persist and query normalized offers."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def upsert(self, product: Product, offer: Offer, analysis: Analysis) -> OfferRow:
        """Insert or update an offer, and append a price history snapshot."""
        row = (
            self.session.query(OfferRow)
            .filter(OfferRow.offer_id == offer.offer_id, OfferRow.source == offer.source.value)
            .first()
        )

        if row is None:
            row = OfferRow()
            self.session.add(row)

        # Product fields
        row.offer_id = offer.offer_id
        row.source = offer.source.value
        row.product_id = product.canonical_product_id
        row.title = product.title
        row.brand = product.brand
        row.model_name = product.model
        row.canonical_category = product.canonical_category
        # Condition
        row.condition_canonical = offer.condition.canonical.value
        row.condition_source_label = offer.condition.source_label
        row.functional_state = offer.condition.functional_state.value
        row.cosmetic_grade = offer.condition.cosmetic_grade.value
        # Pricing
        row.list_amount = offer.pricing.list_amount
        row.sale_amount = offer.pricing.sale_amount
        row.currency = offer.pricing.currency
        row.shipping_amount = offer.pricing.shipping_amount
        row.total_landed_cost = offer.pricing.total_landed_cost
        # Delivery
        row.earliest_delivery_at = offer.delivery.earliest_delivery_at
        row.latest_delivery_at = offer.delivery.latest_delivery_at
        row.pickup_available = offer.delivery.pickup_available
        # Merchant
        row.seller_name = offer.merchant.seller_name
        row.marketplace = offer.merchant.marketplace
        row.seller_type = offer.merchant.seller_type.value
        # Scoring
        row.overall_score = analysis.overall_score
        row.score_components_json = analysis.components.model_dump_json()
        row.explanation = analysis.explanation
        # Meta
        row.url = offer.url
        row.observed_at = offer.observed_at
        row.raw_json = json.dumps(offer.raw_source_ref) if offer.raw_source_ref else None

        self.session.flush()

        # Append price history snapshot
        history = PriceHistoryRow(
            offer_row_id=row.id,
            list_amount=offer.pricing.list_amount,
            sale_amount=offer.pricing.sale_amount,
            shipping_amount=offer.pricing.shipping_amount,
            total_landed_cost=offer.pricing.total_landed_cost,
            currency=offer.pricing.currency,
            available=True,
        )
        self.session.add(history)

        return row

    def get_by_offer_id(self, offer_id: str) -> Optional[OfferRow]:
        """Look up an offer by its canonical offer_id."""
        return (
            self.session.query(OfferRow).filter(OfferRow.offer_id == offer_id).first()
        )

    def get_price_history(
        self, offer_id: str, days: int = 30
    ) -> list[PriceHistoryRow]:
        """Return price history snapshots for the given offer over N days."""
        cutoff = datetime.utcnow() - timedelta(days=days)
        row = self.get_by_offer_id(offer_id)
        if row is None:
            return []
        return (
            self.session.query(PriceHistoryRow)
            .filter(
                PriceHistoryRow.offer_row_id == row.id,
                PriceHistoryRow.recorded_at >= cutoff,
            )
            .order_by(PriceHistoryRow.recorded_at)
            .all()
        )

    def get_price_stats(
        self, offer_id: str, days: int = 30
    ) -> dict[str, Optional[float]]:
        """Return min/max/median total landed cost over a window."""
        history = self.get_price_history(offer_id, days)
        costs = [h.total_landed_cost for h in history if h.total_landed_cost is not None]
        if not costs:
            return {"min": None, "max": None, "median": None, "count": 0}
        costs.sort()
        n = len(costs)
        median = costs[n // 2] if n % 2 else (costs[n // 2 - 1] + costs[n // 2]) / 2
        return {
            "min": min(costs),
            "max": max(costs),
            "median": median,
            "count": n,
        }


# ── Watch Repository ───────────────────────────────────────────────


class WatchRepo:
    """Persist and query saved watches."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, watch: Watch) -> WatchRow:
        """Insert a new watch."""
        row = WatchRow(
            watch_id=watch.watch_id,
            raw_query=watch.raw_query,
            budget=watch.budget,
            country=watch.country,
            postal_code=watch.postal_code,
            currency=watch.currency,
            top_n=watch.top_n,
            schedule=watch.schedule,
            timezone=watch.timezone,
            email=watch.email,
            status=watch.status.value,
            created_at=watch.created_at,
            subscription_status=watch.subscription_status,
            digest_frequency=watch.digest_frequency,
        )
        row.set_conditions([c.value for c in watch.conditions])
        row.set_triggers([t.model_dump() for t in watch.triggers])
        self.session.add(row)
        self.session.flush()
        return row

    def get(self, watch_id: str) -> Optional[WatchRow]:
        """Look up a watch by ID."""
        return (
            self.session.query(WatchRow)
            .filter(WatchRow.watch_id == watch_id)
            .first()
        )

    def list_active(self) -> list[WatchRow]:
        """Return all active watches."""
        return (
            self.session.query(WatchRow)
            .filter(WatchRow.status == WatchStatus.ACTIVE.value)
            .order_by(WatchRow.created_at.desc())
            .all()
        )

    def list_all(self) -> list[WatchRow]:
        """Return all non-deleted watches."""
        return (
            self.session.query(WatchRow)
            .filter(WatchRow.status != WatchStatus.DELETED.value)
            .order_by(WatchRow.created_at.desc())
            .all()
        )

    def update_status(self, watch_id: str, status: WatchStatus) -> bool:
        """Update a watch's lifecycle status."""
        row = self.get(watch_id)
        if row is None:
            return False
        row.status = status.value
        return True

    def update_last_run(self, watch_id: str, run_at: datetime) -> bool:
        """Record when a watch was last executed."""
        row = self.get(watch_id)
        if row is None:
            return False
        row.last_run_at = run_at
        return True

    def log_run(
        self,
        watch_id: str,
        started_at: datetime,
        finished_at: datetime,
        results_count: int,
        alerts_fired: bool,
        errors: list[str] | None = None,
    ) -> WatchRunRow:
        """Log a completed watch run."""
        run = WatchRunRow(
            watch_id=watch_id,
            started_at=started_at,
            finished_at=finished_at,
            status="success" if not errors else "failed",
            results_count=results_count,
            alerts_fired=alerts_fired,
            errors_json=json.dumps(errors) if errors else None,
        )
        self.session.add(run)
        return run
