"""Mock LLM client that returns canned structured outputs.

Used when ``TECHWATCH_MOCK=true`` so the full pipeline runs without an
OpenAI API key. Returns plausible planner and explainer outputs.
"""

from __future__ import annotations

import logging
from typing import Any, TypeVar

from pydantic import BaseModel

from techwatch.models import SearchPlan
from techwatch.models.enums import CanonicalCondition
from techwatch.models.narrative import OfferNarrative

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# ── Canned responses ────────────────────────────────────────────────


_CANNED_PLANS: dict[str, dict[str, Any]] = {
    "default": {
        "canonical_category": "laptop",
        "keywords": ["thinkpad", "x1", "carbon"],
        "required_specs": {"ram_gb": 16},
        "excluded_specs": {},
        "budget_max": 900.0,
        "budget_currency": "USD",
        "conditions": ["new", "open_box", "certified_refurbished", "used_good"],
        "preferred_sources": [],
        "country": "US",
        "postal_code": None,
        "reasoning": (
            "The user is looking for a ThinkPad X1 Carbon, a premium business "
            "ultrabook. Budget of $900 suggests willingness to consider used or "
            "open-box alongside new. Prioritizing 16GB RAM as X1 Carbons are "
            "soldered. Searching Best Buy for new/open-box and eBay for used "
            "and certified refurbished listings."
        ),
    }
}

_CANNED_NARRATIVES: list[dict[str, str]] = [
    {
        "headline": "Strong deal on a current-gen ThinkPad with full warranty",
        "value_insight": (
            "This open-box unit is 39% off the $1,449 retail price — significantly "
            "below the 30-day average for this SKU."
        ),
        "condition_insight": (
            "Open-Box Excellent Certified means the device has been inspected by "
            "Best Buy, has no cosmetic damage, and comes with a full manufacturer warranty."
        ),
        "delivery_insight": "Available for in-store pickup today or free standard shipping.",
        "recommendation": (
            "This is likely the best value in the results — current-gen i7, 16GB, "
            "512GB at a used-market price point but with full warranty coverage."
        ),
        "caveats": "Open-box stock is limited and unpredictable. Act quickly if interested.",
    },
    {
        "headline": "Budget-friendly certified refurb from official seller",
        "value_insight": (
            "At $749.99 with free shipping, this certified refurbished listing is "
            "well within the $900 budget with room to spare."
        ),
        "condition_insight": (
            "eBay Certified Refurbished from the official Lenovo outlet includes "
            "a 2-year warranty and free returns. Functionality is guaranteed."
        ),
        "delivery_insight": "Free standard shipping. No in-store pickup option.",
        "recommendation": (
            "Excellent choice for a buyer who wants warranty protection at a "
            "significant discount. The seller's 99.8% feedback is top-tier."
        ),
        "caveats": (
            "Refurbished means the device was previously owned. Battery health "
            "may vary from a new unit."
        ),
    },
    {
        "headline": "Deep discount on older-gen model — great for basic use",
        "value_insight": (
            "The Gen 9 at $549 offers excellent value if you don't need the latest "
            "processor. The 32GB RAM and 1TB SSD are premium specs."
        ),
        "condition_insight": (
            "Listed as 'Used - Excellent' by a high-feedback seller. No warranty "
            "beyond eBay Money Back Guarantee."
        ),
        "delivery_insight": "Ships via standard shipping for $12.99.",
        "recommendation": (
            "Best option for a power user on a budget who needs RAM and storage "
            "over CPU performance."
        ),
        "caveats": (
            "No manufacturer warranty. The i7-1185G7 is 3 generations old. "
            "Battery degradation is likely on a Gen 9 unit."
        ),
    },
]


class MockLlmClient:
    """Drop-in replacement for LlmClient that returns canned data."""

    def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        response_model: type[T],
        tools: list[dict[str, Any]] | None = None,
        temperature: float | None = None,
    ) -> T:
        """Return a canned response matching the response_model."""
        logger.info("[MOCK] LLM structured_completion for %s", response_model.__name__)

        if response_model is SearchPlan or response_model.__name__ == "SearchPlan":
            data = dict(_CANNED_PLANS["default"])
            # Try to incorporate actual query keywords
            if "thinkpad" not in user_prompt.lower():
                # Extract keywords from the user prompt
                for line in user_prompt.split("\n"):
                    if line.startswith("User search query:"):
                        query_text = line.split(":", 1)[1].strip().strip('"')
                        data["keywords"] = query_text.split()[:5]
                        break
            return response_model.model_validate(data)  # type: ignore[return-value]

        if response_model is OfferNarrative or response_model.__name__ == "OfferNarrative":
            import hashlib
            # Deterministically pick a narrative based on the prompt content
            idx = int(hashlib.md5(user_prompt.encode()).hexdigest(), 16) % len(
                _CANNED_NARRATIVES
            )
            return response_model.model_validate(
                _CANNED_NARRATIVES[idx]
            )  # type: ignore[return-value]

        # Fallback: try to create a default instance
        return response_model()  # type: ignore[return-value]

    def chat(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float | None = None,
    ) -> str:
        """Return a canned plain-text response."""
        logger.info("[MOCK] LLM chat completion")
        return (
            "Based on the analysis, this appears to be a competitive offer "
            "in the current market. The pricing is within expected ranges for "
            "this product category and condition."
        )

    def close(self) -> None:
        pass
