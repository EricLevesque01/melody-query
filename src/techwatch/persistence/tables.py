"""SQLAlchemy table definitions for TechWatch persistence."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Declarative base for all TechWatch tables."""


# ── Offers ──────────────────────────────────────────────────────────


class OfferRow(Base):
    """Persisted offer snapshot."""

    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    offer_id = Column(String(255), nullable=False, index=True)
    source = Column(String(50), nullable=False)
    product_id = Column(String(255), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    brand = Column(String(255), nullable=True)
    model_name = Column(String(255), nullable=True)
    canonical_category = Column(String(100), nullable=False)
    # Condition (3-axis)
    condition_canonical = Column(String(50), nullable=False, default="unknown")
    condition_source_label = Column(String(100), nullable=True)
    functional_state = Column(String(50), nullable=False, default="unknown")
    cosmetic_grade = Column(String(50), nullable=False, default="unknown")
    # Pricing
    list_amount = Column(Float, nullable=True)
    sale_amount = Column(Float, nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    shipping_amount = Column(Float, nullable=False, default=0.0)
    total_landed_cost = Column(Float, nullable=True)
    # Delivery
    earliest_delivery_at = Column(DateTime, nullable=True)
    latest_delivery_at = Column(DateTime, nullable=True)
    pickup_available = Column(Boolean, nullable=False, default=False)
    # Merchant
    seller_name = Column(String(255), nullable=True)
    marketplace = Column(String(100), nullable=False)
    seller_type = Column(String(50), nullable=False, default="unknown")
    # Scoring
    overall_score = Column(Float, nullable=True)
    score_components_json = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    # Meta
    url = Column(Text, nullable=True)
    observed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    raw_json = Column(Text, nullable=True)

    # Relationships
    history = relationship("PriceHistoryRow", back_populates="offer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_offers_source_product", "source", "product_id"),
        Index("ix_offers_category", "canonical_category"),
    )


# ── Price History ───────────────────────────────────────────────────


class PriceHistoryRow(Base):
    """Point-in-time price snapshot for trend analysis."""

    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    offer_row_id = Column(Integer, ForeignKey("offers.id"), nullable=False)
    list_amount = Column(Float, nullable=True)
    sale_amount = Column(Float, nullable=True)
    shipping_amount = Column(Float, nullable=False, default=0.0)
    total_landed_cost = Column(Float, nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    available = Column(Boolean, nullable=False, default=True)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    offer = relationship("OfferRow", back_populates="history")


# ── Watches ─────────────────────────────────────────────────────────


class WatchRow(Base):
    """Persisted saved search / watch configuration."""

    __tablename__ = "watches"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(String(12), nullable=False, unique=True, index=True)
    raw_query = Column(String(500), nullable=False)
    budget = Column(Float, nullable=True)
    country = Column(String(10), nullable=False, default="US")
    postal_code = Column(String(20), nullable=True)
    currency = Column(String(10), nullable=False, default="USD")
    conditions_json = Column(Text, nullable=False, default="[]")
    top_n = Column(Integer, nullable=False, default=10)
    schedule = Column(String(100), nullable=False, default="0 9 * * *")
    timezone = Column(String(100), nullable=False, default="America/New_York")
    email = Column(String(255), nullable=True)
    triggers_json = Column(Text, nullable=False, default="[]")
    status = Column(String(20), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_run_at = Column(DateTime, nullable=True)
    next_run_at = Column(DateTime, nullable=True)
    subscription_status = Column(String(20), nullable=False, default="subscribed")
    digest_frequency = Column(String(20), nullable=False, default="per_trigger")
    last_opt_out_at = Column(DateTime, nullable=True)

    # Convenience helpers for JSON fields
    def get_conditions(self) -> list[str]:
        return json.loads(self.conditions_json) if self.conditions_json else []

    def set_conditions(self, conditions: list[str]) -> None:
        self.conditions_json = json.dumps(conditions)

    def get_triggers(self) -> list[dict]:
        return json.loads(self.triggers_json) if self.triggers_json else []

    def set_triggers(self, triggers: list[dict]) -> None:
        self.triggers_json = json.dumps(triggers)


# ── Watch Run Log ───────────────────────────────────────────────────


class WatchRunRow(Base):
    """Log of each watch execution for auditing and debugging."""

    __tablename__ = "watch_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_id = Column(String(12), ForeignKey("watches.watch_id"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running, success, failed
    results_count = Column(Integer, nullable=False, default=0)
    alerts_fired = Column(Boolean, nullable=False, default=False)
    errors_json = Column(Text, nullable=True)
