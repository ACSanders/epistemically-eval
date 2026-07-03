"""Central allowed-label vocabulary for model outputs.

Exact-label scoring is only meaningful if the model answers from a fixed
vocabulary. This map is prompt-side control: build_prompt() lists these
values for each requested field, and invalid_label_values() flags
off-vocabulary answers in result rows. It is deliberately not enforced in
the case schema — cases may introduce new fields, which fall back to
free-string prompting until they are added here.
"""

from typing import Any, Dict, List, Mapping

# Values cover the labels used in data/cases/*.jsonl, plus natural
# complements where the used set would otherwise leave the model no way to
# disagree (e.g. failure_mode "none").
ALLOWED_LABELS: Dict[str, List[str]] = {
    "belief_status": ["believes", "does_not_believe"],
    "truth_status": ["true", "false"],
    "justification_status": [
        "justified",
        "unjustified",
        "initially_supported_but_defective",
    ],
    "knowledge_status": ["knows", "does_not_know"],
    "epistemic_status": [
        "knowledge",
        "true_belief",
        "false_belief",
        "no_belief",
        "lucky_true_belief",
        "valid_inference",
        "invalid_inference",
        "inconsistent_commitments",
    ],
    "failure_mode": ["epistemic_luck", "none"],
    "inference_type": [
        "modus_ponens",
        "modus_tollens",
        "affirming_the_consequent",
        "denying_the_antecedent",
        "disjunctive_syllogism",
        "hypothetical_syllogism",
        "contradiction_detection",
    ],
    "validity": ["valid", "invalid"],
    "conclusion_follows": ["true", "false"],
    "rational_requirement": ["accept_target_or_revise_prior_commitments", "none"],
    "incoherence_if_rejects_target": ["true", "false"],
    "contradiction_present": ["true", "false"],
    "consistency_status": ["consistent", "inconsistent"],
    "initial_status": ["justified_belief", "unjustified_belief", "no_belief"],
    # Mainstream categories only; finer distinctions (source reliability,
    # dependency) live in schema_family, and defeater_type is diagnostic
    # rather than part of the primary score in v0.
    "defeater_type": [
        "none_placebo",
        "rebutting_defeater",
        "undercutting_defeater",
        "higher_order_defeater",
        "unclear",
    ],
    # v0 keeps belief-revision options coarse; finer retain/suspend
    # distinctions can come later.
    "updated_status": [
        "retain_belief",
        "reduce_confidence",
        "believe_not_p",
        "unclear",
    ],
    "retain_original_belief": ["yes", "no"],
    "confidence_direction": ["increase", "decrease", "unchanged"],
}


def _comparable(value: Any) -> str:
    """Render a label value in the form used for vocabulary comparison."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value).strip().lower()


def invalid_label_values(predicted: Mapping[str, Any]) -> Dict[str, Any]:
    """Flag predicted values that fall outside the allowed vocabulary.

    Returns {field: offending_value} for every field that has an allowed
    vocabulary but whose predicted value is not in it. Fields without a
    vocabulary entry and brief_explanation are ignored. Diagnostic only —
    this does not affect scoring.
    """
    invalid: Dict[str, Any] = {}
    for field, value in predicted.items():
        allowed = ALLOWED_LABELS.get(field)
        if allowed is None:
            continue
        if _comparable(value) not in {v.lower() for v in allowed}:
            invalid[field] = value
    return invalid
