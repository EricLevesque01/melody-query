"""Search-related models — planner output and result containers."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from techwatch.models.analysis import Analysis
from techwatch.models.enums import CanonicalCondition, Source
from techwatch.models.offer import Offer
from techwatch.models.product import Product


class SearchPlan(BaseModel):
    """Structured output from the Planner agent.

    Represents the agent's interpretation of the user's intent,
    decomposed into actionable search parameters.
    """

    model_config = ConfigDict(strict=True)

    canonical_category: str
    keywords: list[str] = []
    required_specs: dict[str, str | int | float | bool] = {}
    excluded_specs: dict[str, str | int | float | bool] = {}
    budget_max: Optional[float] = None
    budget_currency: str = "USD"
    conditions: list[CanonicalCondition] = [CanonicalCondition.NEW]
    preferred_sources: list[Source] = []
    country: str = "US"
    postal_code: Optional[str] = None
    reasoning: str = ""


class SearchQuery(BaseModel):
    """User-facing search parameters (CLI input)."""

    model_config = ConfigDict(strict=True)

    raw_query: str
    budget: Optional[float] = None
    country: str = "US"
    postal_code: Optional[str] = None
    currency: str = "USD"
    conditions: list[CanonicalCondition] = Field(
        default_factory=lambda: list(CanonicalCondition)
    )
    top_n: int = 10


class SearchResult(BaseModel):
    """A single scored search result pairing product + offer + analysis."""

    model_config = ConfigDict(strict=True)

    product: Product
    offer: Offer
    analysis: Analysis = Analysis()
    rank: int = 0


class SearchResponse(BaseModel):
    """Complete response for a search operation."""

    model_config = ConfigDict(strict=True)

    query: SearchQuery
    plan: Optional[SearchPlan] = None
    results: list[SearchResult] = []
    total_found: int = 0
    sources_queried: list[Source] = []
    errors: list[str] = []
