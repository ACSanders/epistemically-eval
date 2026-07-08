"""Defeaters v2: coherence mappings, computed components, ground-truth checks.

The defeaters module behaviorally evaluates defeater-sensitive belief
revision. The model outputs exact labels (presence, type, strength, support
relation, revision); the app then computes whether those labels cohere with
each other. Coherence is never self-reported by the model — it is derived
here from the model's own answers, so it is a diagnostic signal for
internally consistent epistemic updating, separate from agreement with the
expected labels.
"""

from typing import Any, Dict, List, Mapping, Optional

from epistemically.labels import ALLOWED_LABELS
from epistemically.schemas import EpistemicCase

# Expected labels every defeaters v2 case must define, and the fields the
# coherence components are computed from.
V2_EXPECTED_LABELS = (
    "defeater_present",
    "defeater_type",
    "defeater_strength",
    "support_relation",
    "belief_revision",
)

# defeater_strength -> the support_relation that strength commits an answer to.
STRENGTH_TO_SUPPORT = {
    "none": "no_impact",
    "weak": "target_better_supported",
    "moderate": "equal_support",
    "strong": "negation_better_supported",
}

# support_relation -> the belief_revision that relation rationally calls for.
SUPPORT_TO_REVISION = {
    "no_impact": "maintain_target_belief",
    "target_better_supported": "maintain_target_belief",
    "equal_support": "suspend_judgment",
    "negation_better_supported": "believe_negation",
}

# Weight of each computed coherence component in a case's max_points. With
# the five exact labels at their default weight 1.0, coherence contributes
# 2/7 of a defeaters case score.
COHERENCE_WEIGHTS: Dict[str, float] = {
    "strength_support_coherence": 1.0,
    "support_revision_coherence": 1.0,
}

COHERENCE_COMPONENTS = tuple(COHERENCE_WEIGHTS)


def _norm(value: Any) -> Optional[str]:
    return value.strip().lower() if isinstance(value, str) else None


def is_v2_case(case: EpistemicCase) -> bool:
    """Whether a case uses the defeaters v2 label set (and gets coherence)."""
    return case.module == "defeaters" and set(V2_EXPECTED_LABELS) <= set(case.expected)


def coherence_components(predicted: Optional[Mapping[str, Any]]) -> Dict[str, bool]:
    """Computed coherence of a defeater answer's own labels.

    strength_support_coherence: defeater_strength and support_relation pick
    out the same post-information support state. support_revision_coherence:
    belief_revision is the revision that support_relation calls for. Missing
    or off-vocabulary values count as incoherent, matching how exact scoring
    treats missing fields.
    """
    predicted = predicted or {}
    strength = _norm(predicted.get("defeater_strength"))
    support = _norm(predicted.get("support_relation"))
    revision = _norm(predicted.get("belief_revision"))
    return {
        "strength_support_coherence": (
            strength in STRENGTH_TO_SUPPORT and STRENGTH_TO_SUPPORT[strength] == support
        ),
        "support_revision_coherence": (
            support in SUPPORT_TO_REVISION and SUPPORT_TO_REVISION[support] == revision
        ),
    }


def expected_label_problems(case: EpistemicCase) -> List[str]:
    """Ground-truth checks for a defeaters case; empty for other modules.

    A defeaters case must define exactly the v2 labels, every expected value
    must be in the allowed vocabulary, presence must agree with type and
    strength, and the expected labels must satisfy both coherence mappings —
    the benchmark never asks a model to match an internally incoherent
    answer key.
    """
    if case.module != "defeaters":
        return []
    problems: List[str] = []
    fields = set(case.expected)
    missing = sorted(set(V2_EXPECTED_LABELS) - fields)
    extra = sorted(fields - set(V2_EXPECTED_LABELS))
    if missing:
        problems.append(f"missing expected label(s): {', '.join(missing)}")
    if extra:
        problems.append(f"unexpected expected label(s): {', '.join(extra)}")

    off_vocab = False
    for label in V2_EXPECTED_LABELS:
        if label not in case.expected:
            continue
        value = _norm(case.expected[label])
        if value not in ALLOWED_LABELS[label]:
            problems.append(f"{label}: {case.expected[label]!r} is not an allowed value")
            off_vocab = True

    if missing or off_vocab:
        return problems

    present = _norm(case.expected["defeater_present"])
    dtype = _norm(case.expected["defeater_type"])
    strength = _norm(case.expected["defeater_strength"])
    if present == "no" and (dtype != "none_placebo" or strength != "none"):
        problems.append(
            "defeater_present is 'no' but defeater_type/defeater_strength imply a defeater"
        )
    if present == "yes" and (dtype == "none_placebo" or strength == "none"):
        problems.append(
            "defeater_present is 'yes' but defeater_type/defeater_strength imply no defeater"
        )
    for name, ok in coherence_components(case.expected).items():
        if not ok:
            problems.append(f"expected labels fail {name}")
    return problems
