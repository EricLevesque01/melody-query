"""Planner agent — converts user intent into a structured SearchPlan."""

from __future__ import annotations

import logging

from techwatch.agents.llm_client import LlmClient
from techwatch.models import SearchPlan, SearchQuery

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """\
You are a tech product research planner. Your job is to convert a user's
natural language search intent into a structured search plan.

Given a user query, produce a SearchPlan with:
- canonical_category: the best product category (e.g. "laptop", "monitor", "phone", "tablet", "headphones", "keyboard", "mouse", "gpu", "cpu", "ssd", "ram")
- keywords: specific search keywords extracted from the query
- required_specs: specs the product MUST have (e.g. {"ram_gb": 16, "cpu": "Apple M3"})
- excluded_specs: specs to avoid
- budget_max: maximum price if mentioned
- budget_currency: currency for the budget
- conditions: list of acceptable conditions (new, open_box, certified_refurbished, refurbished, used_like_new, used_good, used_fair)
- preferred_sources: which sources to prioritize (bestbuy, ebay, structured_web)
- country: buyer's country
- postal_code: buyer's postal code if known
- reasoning: brief explanation of how you interpreted the query

Be specific about specs. If the user says "16GB RAM", set required_specs.ram_gb = 16.
If they say "under $700", set budget_max = 700.
If they mention "used" or "refurbished", include those conditions.
If no conditions are mentioned, include all conditions.
"""


class PlannerAgent:
    """Converts user intent into a structured SearchPlan.

    Uses OpenAI structured outputs to guarantee the plan validates
    against the SearchPlan Pydantic schema.
    """

    def __init__(self, llm: LlmClient | None = None) -> None:
        self._llm = llm or LlmClient()

    def plan(self, query: SearchQuery) -> SearchPlan:
        """Convert a SearchQuery into a SearchPlan."""
        user_prompt = self._build_prompt(query)

        plan = self._llm.structured_completion(
            system_prompt=PLANNER_SYSTEM_PROMPT,
            user_prompt=user_prompt,
            response_model=SearchPlan,
        )

        logger.info(
            "Planner: category=%s keywords=%s budget=%s conditions=%s",
            plan.canonical_category,
            plan.keywords,
            plan.budget_max,
            [c.value for c in plan.conditions],
        )
        return plan

    def _build_prompt(self, query: SearchQuery) -> str:
        parts = [f'User search query: "{query.raw_query}"']
        if query.budget:
            parts.append(f"Budget: {query.currency} {query.budget}")
        parts.append(f"Country: {query.country}")
        if query.postal_code:
            parts.append(f"Postal code: {query.postal_code}")
        if query.conditions:
            parts.append(
                f"Acceptable conditions: {', '.join(c.value for c in query.conditions)}"
            )
        return "\n".join(parts)

    def close(self) -> None:
        self._llm.close()
