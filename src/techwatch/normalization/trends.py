"""Price trend analysis — compute analytics from price history snapshots.

All calculations are deterministic Python. No LLM calls.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from techwatch.persistence.tables import PriceHistoryRow


@dataclass(frozen=True)
class PriceTrend:
    """Computed price trend for a single offer over a time window."""

    offer_id: str
    window_days: int
    data_points: int
    current_price: Optional[float]
    min_price: Optional[float]
    max_price: Optional[float]
    mean_price: Optional[float]
    median_price: Optional[float]
    stdev: Optional[float]
    pct_change_vs_first: Optional[float]  # % change from first to last
    pct_below_median: Optional[float]     # how far current is below median
    is_all_time_low: bool = False
    trend_direction: str = "stable"       # "falling", "rising", "stable", "volatile"


def compute_trend(
    offer_id: str,
    history: list[PriceHistoryRow],
    *,
    window_days: int = 30,
) -> PriceTrend:
    """Compute price trend analytics from history snapshots."""
    costs = [
        h.total_landed_cost for h in history
        if h.total_landed_cost is not None
    ]

    if not costs:
        return PriceTrend(
            offer_id=offer_id,
            window_days=window_days,
            data_points=0,
            current_price=None,
            min_price=None,
            max_price=None,
            mean_price=None,
            median_price=None,
            stdev=None,
            pct_change_vs_first=None,
            pct_below_median=None,
        )

    current = costs[-1]
    min_price = min(costs)
    max_price = max(costs)
    mean_price = statistics.mean(costs)
    median_price = statistics.median(costs)
    stdev = statistics.stdev(costs) if len(costs) >= 2 else 0.0

    # Percentage change from first observation to current
    first = costs[0]
    pct_change = ((current - first) / first * 100) if first > 0 else None

    # How far below median
    pct_below_median = (
        ((median_price - current) / median_price * 100)
        if median_price > 0
        else None
    )

    # Determine trend direction
    if len(costs) < 3:
        direction = "stable"
    else:
        # Use linear slope approximation
        recent_half = costs[len(costs) // 2:]
        early_half = costs[:len(costs) // 2]
        recent_mean = statistics.mean(recent_half)
        early_mean = statistics.mean(early_half)

        change_pct = (
            ((recent_mean - early_mean) / early_mean * 100)
            if early_mean > 0 else 0
        )

        if change_pct < -3:
            direction = "falling"
        elif change_pct > 3:
            direction = "rising"
        elif stdev / mean_price > 0.1 if mean_price > 0 else False:
            direction = "volatile"
        else:
            direction = "stable"

    return PriceTrend(
        offer_id=offer_id,
        window_days=window_days,
        data_points=len(costs),
        current_price=current,
        min_price=min_price,
        max_price=max_price,
        mean_price=round(mean_price, 2),
        median_price=round(median_price, 2),
        stdev=round(stdev, 2),
        pct_change_vs_first=round(pct_change, 2) if pct_change is not None else None,
        pct_below_median=round(pct_below_median, 2) if pct_below_median is not None else None,
        is_all_time_low=current <= min_price,
        trend_direction=direction,
    )


@dataclass(frozen=True)
class MarketSnapshot:
    """Aggregate market analytics across multiple offers for a product."""

    product_query: str
    num_offers: int
    price_range: tuple[float, float]
    median_price: float
    best_value_offer_id: Optional[str]
    best_value_score: float
    conditions_available: list[str]


def compute_market_snapshot(
    query: str,
    trends: list[PriceTrend],
    scores: dict[str, float] | None = None,
) -> MarketSnapshot:
    """Compute aggregate market analytics from individual offer trends."""
    current_prices = [
        t.current_price for t in trends
        if t.current_price is not None
    ]

    if not current_prices:
        return MarketSnapshot(
            product_query=query,
            num_offers=0,
            price_range=(0.0, 0.0),
            median_price=0.0,
            best_value_offer_id=None,
            best_value_score=0.0,
            conditions_available=[],
        )

    # Find best value (highest overall score)
    best_id = None
    best_score = 0.0
    if scores:
        for offer_id, score in scores.items():
            if score > best_score:
                best_score = score
                best_id = offer_id

    return MarketSnapshot(
        product_query=query,
        num_offers=len(trends),
        price_range=(min(current_prices), max(current_prices)),
        median_price=round(statistics.median(current_prices), 2),
        best_value_offer_id=best_id,
        best_value_score=best_score,
        conditions_available=[],  # Filled by caller
    )
