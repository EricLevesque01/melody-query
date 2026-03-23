"""Evaluation runner — run golden fixtures and report scoring regressions."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from techwatch.evals.corpus import GoldenFixture, get_golden_fixtures
from techwatch.scoring.scorer import score_result

logger = logging.getLogger(__name__)


@dataclass
class EvalResult:
    """Result of running a single golden fixture."""

    fixture_name: str
    actual_score: float
    expected_min: float
    expected_max: float
    passed: bool
    reason: str = ""


def run_eval(fixture: GoldenFixture) -> EvalResult:
    """Run scoring evaluation against a single golden fixture."""
    analysis = score_result(
        fixture.product,
        fixture.offer,
        fixture.plan,
        budget=fixture.budget,
    )

    score = analysis.overall_score
    passed = fixture.expected_score_min <= score <= fixture.expected_score_max

    reason = ""
    if not passed:
        if score < fixture.expected_score_min:
            reason = f"Score {score:.4f} below expected min {fixture.expected_score_min}"
        else:
            reason = f"Score {score:.4f} above expected max {fixture.expected_score_max}"

    return EvalResult(
        fixture_name=fixture.name,
        actual_score=score,
        expected_min=fixture.expected_score_min,
        expected_max=fixture.expected_score_max,
        passed=passed,
        reason=reason,
    )


def run_ranking_eval(fixtures: list[GoldenFixture]) -> list[str]:
    """Verify relative ranking invariants across fixtures."""
    scores: dict[str, float] = {}
    for f in fixtures:
        analysis = score_result(f.product, f.offer, f.plan, budget=f.budget)
        scores[f.name] = analysis.overall_score

    violations: list[str] = []
    for f in fixtures:
        for lower_name in f.expected_ranking_vs:
            if lower_name in scores:
                if scores[f.name] <= scores[lower_name]:
                    violations.append(
                        f"{f.name} ({scores[f.name]:.4f}) should rank above "
                        f"{lower_name} ({scores[lower_name]:.4f})"
                    )

    return violations


def run_all_evals() -> tuple[list[EvalResult], list[str]]:
    """Run the full evaluation suite."""
    fixtures = get_golden_fixtures()
    results = [run_eval(f) for f in fixtures]
    violations = run_ranking_eval(fixtures)
    return results, violations
