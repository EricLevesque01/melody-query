"""Deal analyst — deterministic alert trigger evaluation."""

from __future__ import annotations

import logging
from typing import Optional

from techwatch.models import AlertDecision, SearchResult, Watch, WatchTrigger
from techwatch.models.enums import TriggerMetric, TriggerOperator
from techwatch.persistence.repos import OfferRepo

logger = logging.getLogger(__name__)


def evaluate_trigger(
    trigger: WatchTrigger,
    result: SearchResult,
    price_stats: dict[str, Optional[float]],
) -> Optional[str]:
    """Evaluate a single trigger against a result. Returns reason string if fired."""
    if trigger.metric == TriggerMetric.PRICE_DROP_PCT:
        median = price_stats.get("median")
        if median and median > 0:
            current = result.offer.pricing.total_landed_cost
            drop_pct = ((median - current) / median) * 100
            if _compare(drop_pct, trigger.operator, trigger.threshold):
                return f"Price dropped {drop_pct:.1f}% vs 30-day median ({median:.2f} -> {current:.2f})"

    elif trigger.metric == TriggerMetric.PRICE_BELOW:
        current = result.offer.pricing.total_landed_cost
        if _compare(current, _invert_op(trigger.operator), trigger.threshold):
            return f"Price {current:.2f} is below threshold {trigger.threshold:.2f}"

    elif trigger.metric == TriggerMetric.NEW_OFFER_RANK:
        if _compare(float(result.rank), trigger.operator, trigger.threshold):
            return f"New offer ranked #{result.rank} (threshold: top {int(trigger.threshold)})"

    elif trigger.metric == TriggerMetric.AVAILABILITY_CHANGE:
        return None  # Requires historical comparison (future)

    return None


def evaluate_watch_triggers(
    watch: Watch,
    results: list[SearchResult],
    offer_repo: OfferRepo,
) -> AlertDecision:
    """Evaluate all triggers for a watch against search results."""
    triggered_rules: list[str] = []
    top_offer_ids: list[str] = []

    for result in results:
        price_stats = offer_repo.get_price_stats(result.offer.offer_id, days=30)

        for trigger_data in watch.triggers:
            reason = evaluate_trigger(trigger_data, result, price_stats)
            if reason:
                triggered_rules.append(reason)
                if result.offer.offer_id not in top_offer_ids:
                    top_offer_ids.append(result.offer.offer_id)

    should_alert = len(triggered_rules) > 0

    headline = ""
    summary = ""
    if should_alert:
        headline = f"{len(triggered_rules)} alert(s) for '{watch.raw_query}'"
        summary = "; ".join(triggered_rules[:5])
        if len(triggered_rules) > 5:
            summary += f" (+{len(triggered_rules) - 5} more)"

    return AlertDecision(
        should_alert=should_alert,
        triggered_rules=triggered_rules,
        headline=headline,
        summary=summary,
        top_offer_ids=top_offer_ids[:10],
    )


def _compare(value: float, operator: TriggerOperator, threshold: float) -> bool:
    if operator == TriggerOperator.GTE:
        return value >= threshold
    elif operator == TriggerOperator.LTE:
        return value <= threshold
    elif operator == TriggerOperator.GT:
        return value > threshold
    elif operator == TriggerOperator.LT:
        return value < threshold
    elif operator == TriggerOperator.EQ:
        return abs(value - threshold) < 0.01
    return False


def _invert_op(op: TriggerOperator) -> TriggerOperator:
    """Invert for 'price below' semantics (price <= threshold)."""
    return TriggerOperator.LTE
