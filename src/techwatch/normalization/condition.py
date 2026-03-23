"""Condition normalization — maps marketplace-specific conditions to canonical 3-axis model.

This module is **deterministic Python only** — no LLM calls.
"""

from __future__ import annotations

from techwatch.models.enums import CanonicalCondition, CosmeticGrade, FunctionalState
from techwatch.models.offer import Condition


# ── Best Buy Open Box ───────────────────────────────────────────────

_BESTBUY_OPEN_BOX_MAP: dict[str, Condition] = {
    "excellent": Condition(
        canonical=CanonicalCondition.OPEN_BOX,
        source_label="Excellent",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.EXCELLENT,
    ),
    "certified": Condition(
        canonical=CanonicalCondition.CERTIFIED_REFURBISHED,
        source_label="Certified",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.PRISTINE,
    ),
    "satisfactory": Condition(
        canonical=CanonicalCondition.OPEN_BOX,
        source_label="Satisfactory",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.FAIR,
    ),
    "fair": Condition(
        canonical=CanonicalCondition.OPEN_BOX,
        source_label="Fair",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.FAIR,
    ),
}


def normalize_bestbuy_condition(condition_label: str) -> Condition:
    """Normalize a Best Buy Open Box condition label."""
    key = condition_label.strip().lower()
    if key in _BESTBUY_OPEN_BOX_MAP:
        return _BESTBUY_OPEN_BOX_MAP[key]
    # Best Buy new items
    if key in ("new", ""):
        return Condition(
            canonical=CanonicalCondition.NEW,
            source_label="New",
            functional_state=FunctionalState.FULLY_FUNCTIONAL,
            cosmetic_grade=CosmeticGrade.PRISTINE,
        )
    return Condition(
        canonical=CanonicalCondition.UNKNOWN,
        source_label=condition_label,
    )


# ── eBay ────────────────────────────────────────────────────────────

_EBAY_CONDITION_MAP: dict[int, Condition] = {
    1000: Condition(
        canonical=CanonicalCondition.NEW,
        source_label="New",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.PRISTINE,
    ),
    1500: Condition(
        canonical=CanonicalCondition.OPEN_BOX,
        source_label="New other",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.EXCELLENT,
    ),
    1750: Condition(
        canonical=CanonicalCondition.NEW,
        source_label="New with defects",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.GOOD,
    ),
    2000: Condition(
        canonical=CanonicalCondition.CERTIFIED_REFURBISHED,
        source_label="Certified Refurbished",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.EXCELLENT,
    ),
    2010: Condition(
        canonical=CanonicalCondition.CERTIFIED_REFURBISHED,
        source_label="Excellent - Refurbished",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.EXCELLENT,
    ),
    2020: Condition(
        canonical=CanonicalCondition.REFURBISHED,
        source_label="Very Good - Refurbished",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.GOOD,
    ),
    2030: Condition(
        canonical=CanonicalCondition.REFURBISHED,
        source_label="Good - Refurbished",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.FAIR,
    ),
    2500: Condition(
        canonical=CanonicalCondition.REFURBISHED,
        source_label="Seller Refurbished",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.GOOD,
    ),
    3000: Condition(
        canonical=CanonicalCondition.USED_LIKE_NEW,
        source_label="Used",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.GOOD,
    ),
    4000: Condition(
        canonical=CanonicalCondition.USED_GOOD,
        source_label="Very Good",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.GOOD,
    ),
    5000: Condition(
        canonical=CanonicalCondition.USED_GOOD,
        source_label="Good",
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=CosmeticGrade.FAIR,
    ),
    6000: Condition(
        canonical=CanonicalCondition.USED_FAIR,
        source_label="Acceptable",
        functional_state=FunctionalState.MINOR_ISSUES,
        cosmetic_grade=CosmeticGrade.FAIR,
    ),
    7000: Condition(
        canonical=CanonicalCondition.FOR_PARTS,
        source_label="For parts or not working",
        functional_state=FunctionalState.FOR_PARTS,
        cosmetic_grade=CosmeticGrade.POOR,
    ),
}


def normalize_ebay_condition(condition_id: int, condition_text: str = "") -> Condition:
    """Normalize an eBay condition ID into canonical 3-axis condition."""
    if condition_id in _EBAY_CONDITION_MAP:
        mapped = _EBAY_CONDITION_MAP[condition_id]
        # Override source_label if eBay provided custom text
        if condition_text:
            return mapped.model_copy(update={"source_label": condition_text})
        return mapped
    return Condition(
        canonical=CanonicalCondition.UNKNOWN,
        source_label=condition_text or f"eBay condition ID {condition_id}",
    )


# ── Back Market ─────────────────────────────────────────────────────

_BACKMARKET_GRADE_MAP: dict[str, CosmeticGrade] = {
    "fair": CosmeticGrade.FAIR,
    "good": CosmeticGrade.GOOD,
    "excellent": CosmeticGrade.EXCELLENT,
    "premium": CosmeticGrade.PREMIUM,
    "stallone": CosmeticGrade.PRISTINE,
}


def normalize_backmarket_condition(grade: str) -> Condition:
    """Normalize a Back Market appearance grade.

    Back Market guarantees 100% functionality for all grades.
    """
    key = grade.strip().lower()
    cosmetic = _BACKMARKET_GRADE_MAP.get(key, CosmeticGrade.UNKNOWN)

    # Map to canonical condition based on cosmetic grade
    if cosmetic in (CosmeticGrade.PREMIUM, CosmeticGrade.PRISTINE):
        canonical = CanonicalCondition.USED_LIKE_NEW
    elif cosmetic == CosmeticGrade.EXCELLENT:
        canonical = CanonicalCondition.REFURBISHED
    elif cosmetic == CosmeticGrade.GOOD:
        canonical = CanonicalCondition.USED_GOOD
    elif cosmetic == CosmeticGrade.FAIR:
        canonical = CanonicalCondition.USED_FAIR
    else:
        canonical = CanonicalCondition.UNKNOWN

    return Condition(
        canonical=canonical,
        source_label=grade,
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=cosmetic,
    )


# ── Swappa ──────────────────────────────────────────────────────────

_SWAPPA_GRADE_MAP: dict[str, tuple[CanonicalCondition, CosmeticGrade]] = {
    "mint": (CanonicalCondition.USED_LIKE_NEW, CosmeticGrade.PRISTINE),
    "good": (CanonicalCondition.USED_GOOD, CosmeticGrade.GOOD),
    "fair": (CanonicalCondition.USED_FAIR, CosmeticGrade.FAIR),
    "new": (CanonicalCondition.NEW, CosmeticGrade.PRISTINE),
}


def normalize_swappa_condition(grade: str) -> Condition:
    """Normalize a Swappa condition grade.

    Swappa requires all items to be fully functional and not activation-locked.
    """
    key = grade.strip().lower()
    canonical, cosmetic = _SWAPPA_GRADE_MAP.get(
        key, (CanonicalCondition.UNKNOWN, CosmeticGrade.UNKNOWN)
    )
    return Condition(
        canonical=canonical,
        source_label=grade,
        functional_state=FunctionalState.FULLY_FUNCTIONAL,
        cosmetic_grade=cosmetic,
    )
