"""Exact-label component scoring.

v0 scores each expected label field for exact correctness after light
normalization, applies per-field weights, and ignores brief_explanation.
"""

from typing import Any, Dict, Optional

from epistemically.schemas import EpistemicCase, ScoreResult

_TRUTHY = {"true", "yes"}
_FALSY = {"false", "no"}


def normalize_label(value: Any) -> Any:
    """Normalize a label value for comparison.

    Booleans pass through; strings like "True"/"yes" become booleans; other
    strings are lowercased and stripped. Anything else is returned as-is.
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _TRUTHY:
            return True
        if lowered in _FALSY:
            return False
        return lowered
    return value


def score_case(case: EpistemicCase, predicted: Optional[Dict[str, Any]]) -> ScoreResult:
    """Score a parsed model response against a case's expected labels.

    Missing fields and a missing/unparseable response count as incorrect.
    brief_explanation is ignored for v0 scoring.
    """
    predicted = predicted or {}
    per_field: Dict[str, bool] = {}
    points = 0.0
    max_points = 0.0

    for label, expected_value in case.expected.items():
        weight = case.weight_for(label)
        max_points += weight
        correct = label in predicted and (
            normalize_label(predicted[label]) == normalize_label(expected_value)
        )
        per_field[label] = correct
        if correct:
            points += weight

    score = points / max_points if max_points > 0 else 0.0
    return ScoreResult(
        per_field=per_field,
        points=points,
        max_points=max_points,
        score=score,
    )
