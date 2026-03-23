"""Deterministic scoring engine.

All scoring is computed from normalized data with explicit, inspectable weights.
No LLM calls — this is the heart of the "deterministic and inspectable" contract.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from techwatch.models import (
    Analysis,
    Offer,
    Product,
    ScoreComponents,
    SearchPlan,
)
from techwatch.models.enums import (
    CanonicalCondition,
    CosmeticGrade,
    FunctionalState,
    SellerType,
    Source,
)


@dataclass(frozen=True)
class ScoringWeights:
    """Configurable weights for the ranking formula."""

    spec_fit: float = 0.35
    value: float = 0.30
    delivery: float = 0.15
    condition: float = 0.10
    trust: float = 0.10

    def validate(self) -> None:
        total = self.spec_fit + self.value + self.delivery + self.condition + self.trust
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")


DEFAULT_WEIGHTS = ScoringWeights()


# ── Individual scoring functions ────────────────────────────────────


def score_spec_fit(product: Product, plan: Optional[SearchPlan]) -> float:
    """Score how well a product's specs match the search plan.

    Returns 0.0–1.0. Higher means better fit.
    """
    if plan is None or not plan.required_specs:
        return 0.5  # No spec requirements → neutral score

    matches = 0
    total = len(plan.required_specs)

    for key, required_value in plan.required_specs.items():
        actual = getattr(product.specs, key, None)
        if actual is None:
            # Check extras
            actual = product.specs.model_extra.get(key) if product.specs.model_extra else None

        if actual is None:
            continue

        if isinstance(required_value, (int, float)) and isinstance(actual, (int, float)):
            # Numeric: score based on how close the actual is to the required
            if actual >= required_value:
                matches += 1
            else:
                matches += actual / required_value  # Partial credit
        elif str(actual).lower() == str(required_value).lower():
            matches += 1

    return min(1.0, matches / total) if total > 0 else 0.5


def score_value(offer: Offer, budget: Optional[float]) -> float:
    """Score the total landed cost relative to budget.

    Returns 0.0–1.0. Lower cost relative to budget scores higher.
    """
    cost = offer.pricing.total_landed_cost
    if cost <= 0:
        return 0.0

    if budget is None or budget <= 0:
        # No budget → invert-normalize to a 0-1 range
        # Assume $2000 as a reasonable max for normalization
        return max(0.0, 1.0 - (cost / 2000.0))

    if cost <= budget:
        # Under budget: score based on how much room is left
        return 0.5 + 0.5 * (1.0 - cost / budget)
    else:
        # Over budget: penalty
        overage = (cost - budget) / budget
        return max(0.0, 0.5 - overage)


def score_delivery(offer: Offer) -> float:
    """Score delivery speed and options.

    Returns 0.0–1.0. Faster delivery and pickup options score higher.
    """
    score = 0.5  # Base score

    if offer.delivery.pickup_available:
        score += 0.2

    if offer.delivery.earliest_delivery_at:
        from datetime import datetime

        days_until = (offer.delivery.earliest_delivery_at - datetime.utcnow()).days
        if days_until <= 1:
            score += 0.3
        elif days_until <= 3:
            score += 0.2
        elif days_until <= 7:
            score += 0.1
        elif days_until > 14:
            score -= 0.1

    return max(0.0, min(1.0, score))


def score_condition(offer: Offer) -> float:
    """Score condition confidence.

    Returns 0.0–1.0. Better condition and higher confidence score higher.
    """
    # Base score from canonical condition
    condition_scores: dict[CanonicalCondition, float] = {
        CanonicalCondition.NEW: 1.0,
        CanonicalCondition.CERTIFIED_REFURBISHED: 0.9,
        CanonicalCondition.OPEN_BOX: 0.85,
        CanonicalCondition.REFURBISHED: 0.75,
        CanonicalCondition.USED_LIKE_NEW: 0.7,
        CanonicalCondition.USED_GOOD: 0.6,
        CanonicalCondition.USED_FAIR: 0.4,
        CanonicalCondition.FOR_PARTS: 0.1,
        CanonicalCondition.UNKNOWN: 0.3,
    }
    score = condition_scores.get(offer.condition.canonical, 0.3)

    # Bonus for confirmed functional state
    if offer.condition.functional_state == FunctionalState.FULLY_FUNCTIONAL:
        score = min(1.0, score + 0.05)
    elif offer.condition.functional_state == FunctionalState.UNKNOWN:
        score = max(0.0, score - 0.05)

    return score


def score_trust(offer: Offer) -> float:
    """Score seller and source trustworthiness.

    Returns 0.0–1.0. Retailers and high-feedback sellers score higher.
    """
    # Base trust by source
    source_trust: dict[Source, float] = {
        Source.BESTBUY: 0.9,
        Source.EBAY: 0.6,
        Source.STRUCTURED_WEB: 0.5,
        Source.MANUAL: 0.3,
    }
    score = source_trust.get(offer.source, 0.5)

    # Seller type adjustment
    if offer.merchant.seller_type == SellerType.RETAILER:
        score = min(1.0, score + 0.1)

    # eBay seller feedback
    if offer.merchant.seller_feedback_pct is not None:
        if offer.merchant.seller_feedback_pct >= 99.0:
            score = min(1.0, score + 0.1)
        elif offer.merchant.seller_feedback_pct < 95.0:
            score = max(0.0, score - 0.15)

    if offer.merchant.seller_feedback_count is not None:
        if offer.merchant.seller_feedback_count >= 1000:
            score = min(1.0, score + 0.05)
        elif offer.merchant.seller_feedback_count < 10:
            score = max(0.0, score - 0.1)

    return max(0.0, min(1.0, score))


# ── Main scorer ─────────────────────────────────────────────────────


def score_result(
    product: Product,
    offer: Offer,
    plan: Optional[SearchPlan] = None,
    budget: Optional[float] = None,
    weights: ScoringWeights = DEFAULT_WEIGHTS,
) -> Analysis:
    """Compute the deterministic ranking score for a product/offer pair.

    Returns an Analysis with individual components and the weighted overall score.
    """
    weights.validate()

    components = ScoreComponents(
        spec_fit=score_spec_fit(product, plan),
        value=score_value(offer, budget),
        delivery=score_delivery(offer),
        condition=score_condition(offer),
        trust=score_trust(offer),
    )

    overall = (
        components.spec_fit * weights.spec_fit
        + components.value * weights.value
        + components.delivery * weights.delivery
        + components.condition * weights.condition
        + components.trust * weights.trust
    )

    return Analysis(
        components=components,
        overall_score=round(overall, 4),
    )
