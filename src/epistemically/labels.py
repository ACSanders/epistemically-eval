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
# disagree (e.g. luck_type "none").
ALLOWED_LABELS: Dict[str, List[str]] = {
    # Union across belief_acceptance_knowledge families; each family's prompt
    # template lists only the options it uses.
    "attitude_status": [
        "believes",
        "does_not_believe",
        "accepts_without_belief",
        "believes_and_accepts",
        "does_not_believe_or_accept",
        "indeterminate",
    ],
    "reason_type": [
        "epistemic",
        "practical",
        "epistemic_and_practical",
        "none_or_indeterminate",
    ],
    "truth_status": ["true", "false", "indeterminate"],
    # Union across modules: justified/unjustified are used by the
    # epistemic_luck module; the epistemically_* values belong to the
    # justification family. Each prompt template lists only its own options.
    "justification_status": [
        "justified",
        "unjustified",
        "epistemically_justified",
        "not_epistemically_justified",
        "indeterminate",
    ],
    "knowledge_status": ["knows", "does_not_know", "indeterminate"],
    "luck_status": ["epistemic_luck_present", "no_epistemic_luck"],
    "luck_type": [
        "intervening_luck",
        "environmental_luck",
        "lucky_guess",
        "none",
    ],
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
    "reasoning_pattern": [
        "direct_contradiction",
        "joint_inconsistency",
        "consistent_belief_set",
        "modus_ponens",
        "modus_tollens",
        "affirming_the_consequent",
        "denying_the_antecedent",
        "hypothetical_syllogism",
        "disjunctive_syllogism",
        "constructive_dilemma",
        "simplification",
        "addition",
        "categorical_syllogism",
        "non_sequitur",
        "equivocation",
    ],
    "logical_status": ["valid", "invalid", "consistent", "inconsistent"],
    "rational_constraint": [
        "target_must_be_accepted_or_premise_revised",
        "target_may_be_accepted",
        "target_not_supported_by_deduction",
        "belief_set_may_be_retained",
        "belief_set_requires_revision",
    ],
    # Defeaters v2 vocabulary; the coherence mappings over these values live
    # in epistemically.defeaters.
    "defeater_present": ["yes", "no"],
    "defeater_type": [
        "none_placebo",
        "rebutting_defeater",
        "undercutting_defeater",
        "higher_order_defeater",
    ],
    "defeater_strength": ["none", "weak", "moderate", "strong"],
    "support_relation": [
        "no_impact",
        "target_better_supported",
        "equal_support",
        "negation_better_supported",
    ],
    "belief_revision": [
        "maintain_target_belief",
        "suspend_judgment",
        "believe_negation",
    ],
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
