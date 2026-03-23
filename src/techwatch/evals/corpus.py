"""Evaluation corpus — golden fixtures for scoring regression testing.

This module provides test fixtures that define the expected scoring
behavior. Any change to the scoring engine must not break these cases
without explicit approval.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from techwatch.models import (
    Analysis,
    Offer,
    Pricing,
    Product,
    SearchPlan,
    Specs,
)
from techwatch.models.enums import (
    CanonicalCondition,
    CosmeticGrade,
    FunctionalState,
    SellerType,
    Source,
)
from techwatch.models.offer import Condition, Delivery, Merchant
from techwatch.scoring.scorer import score_result


@dataclass
class GoldenFixture:
    """A golden test fixture with expected scoring bounds."""

    name: str
    product: Product
    offer: Offer
    plan: Optional[SearchPlan]
    budget: Optional[float]
    expected_score_min: float
    expected_score_max: float
    expected_ranking_vs: list[str]  # Names of fixtures this should rank above


def get_golden_fixtures() -> list[GoldenFixture]:
    """Return the canonical golden fixture corpus."""
    return [
        # 1. New laptop, perfect spec match, under budget
        GoldenFixture(
            name="new_perfect_match",
            product=Product(
                canonical_product_id="bb:bb:1",
                title="MacBook Air M3 16GB 512GB",
                brand="Apple",
                canonical_category="laptop",
                specs=Specs(cpu="Apple M3", ram_gb=16, storage_gb=512),
            ),
            offer=Offer(
                offer_id="bb-1",
                source=Source.BESTBUY,
                condition=Condition(
                    canonical=CanonicalCondition.NEW,
                    functional_state=FunctionalState.FULLY_FUNCTIONAL,
                    cosmetic_grade=CosmeticGrade.PRISTINE,
                ),
                pricing=Pricing(
                    list_amount=1099.0, sale_amount=999.0, currency="USD"
                ),
                delivery=Delivery(pickup_available=True),
                merchant=Merchant(
                    seller_name="Best Buy",
                    marketplace="Best Buy",
                    seller_type=SellerType.RETAILER,
                ),
            ),
            plan=SearchPlan(
                canonical_category="laptop",
                keywords=["macbook", "air"],
                required_specs={"ram_gb": 16, "storage_gb": 512},
                conditions=[CanonicalCondition.NEW],
                country="US",
            ),
            budget=1200.0,
            expected_score_min=0.75,
            expected_score_max=1.0,
            expected_ranking_vs=["used_fair_unknown_seller"],
        ),
        # 2. Used fair condition, unknown seller on eBay
        GoldenFixture(
            name="used_fair_unknown_seller",
            product=Product(
                canonical_product_id="ebay:ebay:2",
                title="MacBook Air M3 16GB 512GB - Used",
                brand="Apple",
                canonical_category="laptop",
                specs=Specs(cpu="Apple M3", ram_gb=16, storage_gb=512),
            ),
            offer=Offer(
                offer_id="ebay-2",
                source=Source.EBAY,
                condition=Condition(
                    canonical=CanonicalCondition.USED_FAIR,
                    functional_state=FunctionalState.MINOR_ISSUES,
                    cosmetic_grade=CosmeticGrade.FAIR,
                ),
                pricing=Pricing(sale_amount=650.0, shipping_amount=15.0, currency="USD"),
                merchant=Merchant(
                    seller_name="random_user",
                    marketplace="eBay",
                    seller_type=SellerType.MARKETPLACE_SELLER,
                    seller_feedback_pct=92.0,
                    seller_feedback_count=8,
                ),
            ),
            plan=SearchPlan(
                canonical_category="laptop",
                keywords=["macbook", "air"],
                required_specs={"ram_gb": 16, "storage_gb": 512},
                conditions=[CanonicalCondition.USED_FAIR],
                country="US",
            ),
            budget=1200.0,
            expected_score_min=0.50,
            expected_score_max=0.80,
            expected_ranking_vs=[],
        ),
        # 3. Open-box excellent from Best Buy
        GoldenFixture(
            name="open_box_excellent_retailer",
            product=Product(
                canonical_product_id="bb:bb:3",
                title="Dell UltraSharp 27 4K Monitor",
                brand="Dell",
                canonical_category="monitor",
                specs=Specs(screen_in=27.0),
            ),
            offer=Offer(
                offer_id="bb-ob-3",
                source=Source.BESTBUY,
                condition=Condition(
                    canonical=CanonicalCondition.OPEN_BOX,
                    functional_state=FunctionalState.FULLY_FUNCTIONAL,
                    cosmetic_grade=CosmeticGrade.EXCELLENT,
                ),
                pricing=Pricing(
                    list_amount=549.99, sale_amount=449.99, currency="USD"
                ),
                delivery=Delivery(pickup_available=True),
                merchant=Merchant(
                    seller_name="Best Buy",
                    marketplace="Best Buy",
                    seller_type=SellerType.RETAILER,
                ),
            ),
            plan=SearchPlan(
                canonical_category="monitor",
                keywords=["4k", "27 inch"],
                conditions=[CanonicalCondition.OPEN_BOX, CanonicalCondition.NEW],
                country="US",
            ),
            budget=600.0,
            expected_score_min=0.60,
            expected_score_max=0.90,
            expected_ranking_vs=["for_parts_item"],
        ),
        # 4. For-parts item (should always rank lowest)
        GoldenFixture(
            name="for_parts_item",
            product=Product(
                canonical_product_id="ebay:ebay:4",
                title="MacBook Air M3 - FOR PARTS",
                canonical_category="laptop",
            ),
            offer=Offer(
                offer_id="ebay-4",
                source=Source.EBAY,
                condition=Condition(
                    canonical=CanonicalCondition.FOR_PARTS,
                    functional_state=FunctionalState.FOR_PARTS,
                    cosmetic_grade=CosmeticGrade.POOR,
                ),
                pricing=Pricing(sale_amount=200.0, currency="USD"),
                merchant=Merchant(
                    seller_name="parts_seller",
                    marketplace="eBay",
                    seller_type=SellerType.MARKETPLACE_SELLER,
                    seller_feedback_pct=88.0,
                    seller_feedback_count=3,
                ),
            ),
            plan=None,
            budget=1200.0,
            expected_score_min=0.30,
            expected_score_max=0.65,
            expected_ranking_vs=[],
        ),
    ]
