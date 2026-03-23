"""Search orchestrator — end-to-end search pipeline.

Coordinates: plan -> select sources -> fetch -> normalize -> score -> explain -> persist
"""

from __future__ import annotations

import logging
from typing import Optional

from techwatch.agents.explainer import ExplainerAgent
from techwatch.agents.llm_client import LlmClient
from techwatch.agents.planner import PlannerAgent
from techwatch.agents.source_selector import select_sources
from techwatch.config import get_settings
from techwatch.models import (
    Analysis,
    SearchPlan,
    SearchQuery,
    SearchResponse,
    SearchResult,
)
from techwatch.models.enums import Source
from techwatch.normalization.engine import (
    normalize_bestbuy_product,
    normalize_ebay_item,
    normalize_jsonld_product,
)
from techwatch.persistence.database import get_session
from techwatch.persistence.repos import OfferRepo
from techwatch.scoring.scorer import score_result

logger = logging.getLogger(__name__)


class SearchOrchestrator:
    """Orchestrates the full search pipeline."""

    def __init__(
        self,
        *,
        llm: LlmClient | None = None,
        skip_llm: bool = False,
    ) -> None:
        settings = get_settings()
        self._mock_mode = settings.mock

        if self._mock_mode:
            from techwatch.agents.mock_llm import MockLlmClient
            self._llm = MockLlmClient()  # type: ignore[assignment]
            logger.info("Orchestrator running in MOCK mode")
        else:
            self._llm = llm or (None if skip_llm else LlmClient())

        self._skip_llm = skip_llm and not self._mock_mode
        self._planner = PlannerAgent(self._llm) if self._llm else None
        self._explainer = ExplainerAgent(self._llm) if self._llm else None

    def search(self, query: SearchQuery) -> SearchResponse:
        """Execute a full search pipeline."""
        errors: list[str] = []
        sources_queried: list[Source] = []

        # 1. Plan
        plan: Optional[SearchPlan] = None
        if self._planner:
            try:
                plan = self._planner.plan(query)
            except Exception as e:
                logger.error("Planner failed: %s", e)
                errors.append(f"Planner error: {e}")
                plan = self._fallback_plan(query)
        else:
            plan = self._fallback_plan(query)

        # 2. Select sources
        selections = select_sources(plan)

        # 3. Fetch and normalize
        all_results: list[SearchResult] = []

        for selection in selections:
            try:
                raw_items = self._fetch_from_adapter(selection.adapter_name, selection.query_params)
                sources_queried.append(selection.source)

                for raw in raw_items:
                    try:
                        pairs = self._normalize(selection.adapter_name, raw)
                        for product, offer in pairs:
                            # 4. Score
                            analysis = score_result(
                                product, offer, plan, budget=query.budget
                            )

                            all_results.append(
                                SearchResult(
                                    product=product,
                                    offer=offer,
                                    analysis=analysis,
                                )
                            )
                    except Exception as e:
                        logger.warning("Normalization error: %s", e)

            except Exception as e:
                logger.error("Adapter %s failed: %s", selection.adapter_name, e)
                errors.append(f"{selection.adapter_name}: {e}")

        # 5. Sort by overall score
        all_results.sort(key=lambda r: r.analysis.overall_score, reverse=True)

        # 6. Assign ranks and trim
        for i, result in enumerate(all_results[: query.top_n]):
            result.rank = i + 1

        top_results = all_results[: query.top_n]

        # 7. Explain top results (optional)
        if self._explainer and top_results:
            for result in top_results[:5]:  # Only explain top 5
                try:
                    narrative = self._explainer.explain(
                        result.product, result.offer, result.analysis
                    )
                    result.analysis.explanation = narrative.headline
                except Exception as e:
                    logger.warning("Explainer error: %s", e)

        # 8. Persist
        self._persist_results(top_results)

        return SearchResponse(
            query=query,
            plan=plan,
            results=top_results,
            total_found=len(all_results),
            sources_queried=list(set(sources_queried)),
            errors=errors,
        )

    def _fallback_plan(self, query: SearchQuery) -> SearchPlan:
        """Create a basic plan without LLM when planner is unavailable."""
        return SearchPlan(
            canonical_category="other",
            keywords=query.raw_query.split(),
            budget_max=query.budget,
            budget_currency=query.currency,
            conditions=query.conditions,
            country=query.country,
            postal_code=query.postal_code,
            reasoning="Fallback plan (no LLM available)",
        )

    def _fetch_from_adapter(
        self, adapter_name: str, params: dict
    ) -> list[dict]:
        """Instantiate and fetch from the named adapter."""
        if self._mock_mode:
            return self._fetch_from_mock_adapter(adapter_name, params)

        if adapter_name == "bestbuy_products":
            from techwatch.adapters.bestbuy.products import BestBuyProductsAdapter
            with BestBuyProductsAdapter() as adapter:
                return adapter.fetch_raw(**params)

        elif adapter_name == "bestbuy_openbox":
            from techwatch.adapters.bestbuy.open_box import BestBuyOpenBoxAdapter
            with BestBuyOpenBoxAdapter() as adapter:
                return adapter.fetch_raw(**params)

        elif adapter_name == "ebay_browse":
            from techwatch.adapters.ebay.browse import EbayBrowseAdapter
            with EbayBrowseAdapter() as adapter:
                return adapter.fetch_raw(**params)

        else:
            logger.warning("Unknown adapter: %s", adapter_name)
            return []

    def _fetch_from_mock_adapter(
        self, adapter_name: str, params: dict
    ) -> list[dict]:
        """Fetch from mock adapters — no network calls."""
        from techwatch.adapters.mock.adapters import (
            MockBestBuyOpenBoxAdapter,
            MockBestBuyProductsAdapter,
            MockEbayBrowseAdapter,
        )

        if adapter_name == "bestbuy_products":
            with MockBestBuyProductsAdapter() as adapter:
                return adapter.fetch_raw(**params)
        elif adapter_name == "bestbuy_openbox":
            with MockBestBuyOpenBoxAdapter() as adapter:
                return adapter.fetch_raw(**params)
        elif adapter_name == "ebay_browse":
            with MockEbayBrowseAdapter() as adapter:
                return adapter.fetch_raw(**params)
        else:
            logger.warning("Unknown mock adapter: %s", adapter_name)
            return []

    def _normalize(
        self, adapter_name: str, raw: dict
    ) -> list[tuple]:
        """Normalize raw data based on adapter type."""
        if adapter_name == "bestbuy_products":
            return [normalize_bestbuy_product(raw)]
        elif adapter_name == "bestbuy_openbox":
            return [normalize_bestbuy_product(raw)]
        elif adapter_name == "ebay_browse":
            return [normalize_ebay_item(raw)]
        elif adapter_name == "structured_web":
            return normalize_jsonld_product(raw)
        return []

    def _persist_results(self, results: list[SearchResult]) -> None:
        """Persist scored results to database."""
        try:
            with get_session() as session:
                repo = OfferRepo(session)
                for result in results:
                    repo.upsert(result.product, result.offer, result.analysis)
        except Exception as e:
            logger.error("Failed to persist results: %s", e)

    def close(self) -> None:
        if self._llm:
            self._llm.close()
