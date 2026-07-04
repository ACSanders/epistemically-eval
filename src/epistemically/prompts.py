"""Prompt construction: turn a case into a structured-JSON-only request."""

import json

from epistemically.labels import ALLOWED_LABELS
from epistemically.schemas import EpistemicCase

SYSTEM_PROMPT = (
    "You evaluate the epistemic status of propositions in short scenarios. "
    "Judge behaviorally and concretely from the information given: what the "
    "agent believes, whether the proposition is true, whether the agent's "
    "position amounts to knowledge, and whether conclusions follow. Do not "
    "over-philosophize; ignore radical-skepticism concerns. Respond with a "
    "single JSON object and nothing else. Every label field must be answered "
    "by copying one value exactly, character for character, from that "
    "field's allowed values; never paraphrase, reword, or invent labels."
)

# Rubric-light primary prompt for the belief_acceptance_knowledge module's
# belief_truth_knowledge family. Deliberately contains no operational theory
# of belief, truth, justification, or knowledge — that lives in the
# methodology docs, not in the tested model's prompt.
BELIEF_TRUTH_KNOWLEDGE_PROMPT = """Your task is to assess a scenario and determine the epistemic position of an agent with respect to a target proposition.

Return exactly four JSON fields:

1. attitude_status
2. truth_status
3. knowledge_status
4. brief_explanation

Allowed labels include:

attitude_status: believes, does_not_believe, indeterminate
truth_status: true, false, indeterminate
knowledge_status: knows, does_not_know, indeterminate

Important considerations for this task:
- Evaluate only the target proposition provided.
- Use the given scenario as the only source of information.
- Use indeterminate as an answer only when the scenario does not provide enough information to classify that field.
- The brief_explanation should be one concise sentence explaining the classification.
- Return JSON only.

Scenario:
{scenario}

Target proposition:
{target_proposition}

Question:
{question}"""

DEFEATER_TYPE_GUIDE = (
    "defeater_type definitions — use these mainstream categories only, not "
    "finer-grained or invented ones:\n"
    '- "none_placebo": the new information is irrelevant to the target '
    "proposition or its support.\n"
    '- "rebutting_defeater": the new information directly supports not-p.\n'
    '- "undercutting_defeater": the new information weakens or breaks the '
    "support relation between the original reason/evidence and p, without "
    "directly proving not-p.\n"
    '- "higher_order_defeater": the new information undermines confidence in '
    "the subject's own reasoning, reliability, judgment, or evidential "
    "handling.\n"
    '- "unclear": the category cannot be determined from the scenario.'
)

RESPONSE_RULES = (
    "Rules:\n"
    "- Output only the JSON object. No prose before or after it.\n"
    "- For each field, the value must be copied exactly from that field's "
    "allowed values, preserving underscores and spelling. Do not paraphrase "
    "labels, do not replace underscores with spaces, do not restate the "
    "proposition, and do not invent new labels.\n"
    "- Fields marked 'true or false' take JSON booleans.\n"
    "- brief_explanation is the only free-text field."
)


def _field_spec(label: str, expected_value) -> str:
    allowed = ALLOWED_LABELS.get(label)
    if allowed:
        options = " | ".join(f'"{value}"' for value in allowed)
        return f'  "{label}": {options}'
    if isinstance(expected_value, bool):
        return f'  "{label}": true or false'
    return f'  "{label}": a short string'


def build_prompt(case: EpistemicCase) -> str:
    """Build the user prompt for one case.

    Asks for a JSON object whose keys mirror the case's expected labels,
    each constrained to its allowed vocabulary where one is defined, plus a
    brief_explanation field (not scored in v0). Cases in the
    belief_acceptance_knowledge module's belief_truth_knowledge family use a
    dedicated rubric-light template instead.
    """
    if (
        case.module == "belief_acceptance_knowledge"
        and case.schema_family == "belief_truth_knowledge"
    ):
        return BELIEF_TRUTH_KNOWLEDGE_PROMPT.format(
            scenario=case.scenario,
            target_proposition=case.target_proposition,
            question=case.question,
        )

    field_lines = [_field_spec(label, value) for label, value in case.expected.items()]
    field_lines.append('  "brief_explanation": one sentence, at most 25 words')
    fields_block = ",\n".join(field_lines)

    guide_block = f"{DEFEATER_TYPE_GUIDE}\n\n" if "defeater_type" in case.expected else ""

    return (
        f"Scenario:\n{case.scenario}\n\n"
        f"Target proposition: {json.dumps(case.target_proposition)}\n\n"
        f"Question: {case.question}\n\n"
        "Answer with a JSON object containing exactly these fields, choosing "
        "each value only from the options shown:\n"
        "{\n"
        f"{fields_block}\n"
        "}\n\n"
        f"{guide_block}"
        f"{RESPONSE_RULES}"
    )
