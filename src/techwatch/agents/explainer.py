"""Explanation agent — generates buyer-facing narratives from deterministic scores."""

from __future__ import annotations

import logging

from techwatch.agents.llm_client import LlmClient
from techwatch.models import Analysis, Offer, Product
from techwatch.models.narrative import OfferNarrative

logger = logging.getLogger(__name__)

EXPLAINER_SYSTEM_PROMPT = """\
You are a tech purchase advisor writing concise buyer-facing explanations.

Given a product, its offer details, and its deterministic score breakdown,
write a clear, helpful narrative that explains:
1. headline: One-sentence summary of the deal
2. value_insight: Why this is or isn't a good value
3. condition_insight: What the condition means for the buyer
4. delivery_insight: Delivery speed and options
5. recommendation: Should the buyer consider this? Why?
6. caveats: Any risks or things to watch out for

IMPORTANT: Do NOT override or contradict the deterministic scores.
Your job is to EXPLAIN them in plain language, not to re-score.
Keep each field to 1-2 sentences maximum.
"""


class ExplainerAgent:
    """Generates buyer-facing explanations from deterministic score data."""

    def __init__(self, llm: LlmClient | None = None) -> None:
        self._llm = llm or LlmClient()

    def explain(
        self, product: Product, offer: Offer, analysis: Analysis
    ) -> OfferNarrative:
        """Generate a narrative explanation for a scored result."""
        user_prompt = (
            f"Product: {product.title}\n"
            f"Brand: {product.brand or 'Unknown'}\n"
            f"Category: {product.canonical_category}\n"
            f"Condition: {offer.condition.canonical.value} "
            f"(source: {offer.condition.source_label}, "
            f"functional: {offer.condition.functional_state.value}, "
            f"cosmetic: {offer.condition.cosmetic_grade.value})\n"
            f"Price: {offer.pricing.currency} {offer.pricing.effective_price:.2f}\n"
            f"Shipping: {offer.pricing.currency} {offer.pricing.shipping_amount:.2f}\n"
            f"Total: {offer.pricing.currency} {offer.pricing.total_landed_cost:.2f}\n"
            f"Marketplace: {offer.merchant.marketplace}\n"
            f"Seller: {offer.merchant.seller_name or 'Unknown'}\n"
            f"Pickup: {'Yes' if offer.delivery.pickup_available else 'No'}\n\n"
            f"Score breakdown:\n"
            f"  Spec fit: {analysis.components.spec_fit:.2f}\n"
            f"  Value: {analysis.components.value:.2f}\n"
            f"  Delivery: {analysis.components.delivery:.2f}\n"
            f"  Condition: {analysis.components.condition:.2f}\n"
            f"  Trust: {analysis.components.trust:.2f}\n"
            f"  Overall: {analysis.overall_score:.3f}\n"
        )

        return self._llm.structured_completion(
            system_prompt=EXPLAINER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=OfferNarrative,
        )

    def close(self) -> None:
        self._llm.close()
