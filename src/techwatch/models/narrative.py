"""Narrative models — LLM-generated buyer-facing explanations."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OfferNarrative(BaseModel):
    """Structured output from the Explanation agent.

    The agent receives deterministic score components and raw offer data
    and produces buyer-facing prose.  It must NOT override or contradict
    the deterministic scores.
    """

    model_config = ConfigDict(strict=True)

    headline: str
    value_insight: str | None = None
    condition_insight: str | None = None
    delivery_insight: str | None = None
    recommendation: str | None = None
    caveats: str | None = None


class DigestEntry(BaseModel):
    """A single item in an email digest."""

    model_config = ConfigDict(strict=True)

    offer_id: str
    title: str
    headline: str
    price_display: str
    condition_display: str
    trigger_reason: str
    url: str | None = None


class DigestPayload(BaseModel):
    """Complete digest ready for rendering into email."""

    model_config = ConfigDict(strict=True)

    watch_id: str
    watch_query: str
    entries: list[DigestEntry] = []
    summary: str = ""
    generated_at_display: str = ""
