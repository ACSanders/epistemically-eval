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

# Rubric-light prompt for the acceptance_and_belief family: separates belief
# from pragmatic acceptance and classifies the agent's reason type.
ACCEPTANCE_AND_BELIEF_PROMPT = """Your task is to assess a scenario and determine the agent's attitude and reason type with respect to a target proposition.

Return exactly four JSON fields:

1. attitude_status
2. reason_type
3. knowledge_status
4. brief_explanation

Allowed labels include:

attitude_status: believes, accepts_without_belief, believes_and_accepts, does_not_believe_or_accept, indeterminate
reason_type: epistemic, practical, epistemic_and_practical, none_or_indeterminate
knowledge_status: knows, does_not_know, indeterminate

Important considerations for this task:
- Evaluate each output field only with respect to the target proposition provided.
- Use the given scenario as the only source of information.
- Use indeterminate or none_or_indeterminate only when the scenario does not provide enough information to classify that field.
- The brief_explanation should be one concise sentence explaining the classification.
- Return JSON only.

Scenario:
{scenario}

Target proposition:
{target_proposition}

Question:
{question}"""

# Rubric-light prompt for the justification family: classifies the agent's
# reason type and epistemic justification status.
JUSTIFICATION_PROMPT = """Your task is to assess a scenario and determine the reason type and epistemic justification status of an agent's belief with respect to a target proposition.

Return exactly four JSON fields:

1. reason_type
2. justification_status
3. knowledge_status
4. brief_explanation

Allowed labels include:

reason_type: epistemic, practical, epistemic_and_practical, none_or_indeterminate
justification_status: epistemically_justified, not_epistemically_justified, indeterminate
knowledge_status: knows, does_not_know, indeterminate

Important considerations for this task:
- Evaluate each output field only with respect to the target proposition provided.
- Use the given scenario as the only source of information.
- Use indeterminate or none_or_indeterminate only when the scenario does not provide enough information to classify that field.
- The brief_explanation should be one concise sentence explaining the classification.
- Return JSON only.

Scenario:
{scenario}

Target proposition:
{target_proposition}

Question:
{question}"""

# Prompt for the epistemic_luck module: justification, knowledge, and
# knowledge-defeating luck under operational labels. JSON braces are doubled
# for str.format.
EPISTEMIC_LUCK_PROMPT = """You are evaluating an epistemic scenario.

Be sure to focus on the target proposition provided in the case. Do not evaluate nearby claims, background claims, or a different proposition.

Return only valid JSON with exactly these fields:

{{
  "justification_status": "...",
  "knowledge_status": "...",
  "luck_status": "...",
  "luck_type": "...",
  "brief_explanation": "..."
}}

Allowed labels:

justification_status:
- justified: The subject has adequate epistemic support for believing the target proposition.
- unjustified: The subject lacks adequate epistemic support for believing the target proposition.

knowledge_status:
- knows: The subject knows the target proposition.
- does_not_know: The subject does not know the target proposition.

luck_status:
- epistemic_luck_present: A knowledge-defeating form of luck is present. The subject's target belief happens to be true in a lucky or accidental way, such that the subject could easily have been wrong given how the belief was formed.
- no_epistemic_luck: No relevant knowledge-defeating epistemic luck is present in the case.

luck_type:
- intervening_luck: The subject's target belief is true, and the subject might have justification, but the belief is true because of some lucky aspect of the case — a lucky break, misleading evidence, a disconnected source, a stale record, a wrong truth-maker, or another accidental connection — rather than because the subject's reason or belief-forming method successfully led them to the target truth. The subject is correct, but in a way that could easily have gone wrong.
- environmental_luck: The subject forms a true belief using a seemingly good belief-forming process, but the surrounding environment or situation they are in is epistemically unsafe. Similar beliefs formed in the exact same way in that particular environment would easily have been false.
- lucky_guess: The subject's target belief is true, but the subject lacks adequate epistemic justification and gets the answer right by guessing or by using an unreliable process.
- none: No relevant knowledge-defeating epistemic luck is present.

Constraints:
- Use only the information provided in the case. Do not assume hidden facts, unstated background probabilities, motives, or extra evidence not stated in the case.
- Do not treat practical desire, convenience, legal consequences, emotional salience, hope, fear, or other pragmatic reasons as epistemic support for the target proposition.
- If the target proposition is false, set knowledge_status to does_not_know.
- Do not classify every false or unsupported belief as epistemic luck. Epistemic luck in this module is knowledge-defeating luck in true-belief cases — lucky guesses, intervening luck, or environmental luck. A plain false belief with no lucky true-belief element is no_epistemic_luck with luck_type none.
- Do not assume that a true belief is knowledge, and do not assume that a justified true belief is always knowledge.
- Do not deny knowledge merely because the scenario is part of an evaluation. Some cases are ordinary knowledge cases with no relevant epistemic luck.
- Use "none" for luck_type when luck_status is "no_epistemic_luck"; use "epistemic_luck_present" when luck_type is "intervening_luck", "environmental_luck", or "lucky_guess".
- Return JSON only. Do not include markdown or extra text. The brief_explanation field should be one concise sentence explaining the classification.

Scenario:
{scenario}

Target proposition:
{target_proposition}

Question:
{question}"""

# Rubric-light prompt for the rational_reasoning module's deduction family:
# reasoning pattern, logical status, and the rational constraint on the agent.
RATIONAL_REASONING_PROMPT = """Your task is to assess a scenario and classify an agent's belief transition or belief set with respect to a target proposition.

Return exactly four JSON fields:

1. reasoning_pattern
2. logical_status
3. rational_constraint
4. brief_explanation

Allowed labels include:

reasoning_pattern: direct_contradiction, joint_inconsistency, consistent_belief_set, modus_ponens, modus_tollens, affirming_the_consequent, denying_the_antecedent, hypothetical_syllogism, disjunctive_syllogism, constructive_dilemma, simplification, addition, categorical_syllogism, non_sequitur, equivocation
logical_status: valid, invalid, consistent, inconsistent
rational_constraint: target_must_be_accepted_or_premise_revised, target_may_be_accepted, target_not_supported_by_deduction, belief_set_may_be_retained, belief_set_requires_revision

Important considerations for this task:
- Focus on the logical relationship among the stated beliefs and the target proposition, not on whether the beliefs are actually true in the real world.
- A conclusion can be deductively valid even when the premises are bizarre or false.
- Do not treat a conclusion as deductively supported merely because it sounds plausible.
- For invalid patterns, classify the target as not supported by deduction even if it might be true for some other reason.
- For consistency cases, evaluate whether the belief set can be coherently retained or requires revision.
- The brief_explanation should be one concise sentence explaining the classification.
- Return JSON only.

Scenario:
{scenario}

Target proposition:
{target_proposition}

Question:
{question}"""

# Prompt for the defeaters v2 module: presence, type, strength, the
# post-information support relation, and the rational belief revision.
# Coherence between these labels is computed and scored by the app
# (epistemically.defeaters); it is never requested from the model. JSON
# braces are doubled for str.format.
DEFEATERS_PROMPT = """You are evaluating how new information should affect an agent's epistemic position with respect to a target proposition.

The target proposition is p; its negation is not-p. The agent initially has some support for p and then receives new information. Use only the information provided in the case. Do not assume additional facts, hidden evidence, unstated background probabilities, motives, or context not specified in the case. Evaluate the rational update from the agent's perspective after receiving the new information.

Return only valid JSON with exactly these fields:

{{
  "defeater_present": "...",
  "defeater_type": "...",
  "defeater_strength": "...",
  "support_relation": "...",
  "belief_revision": "...",
  "brief_explanation": "..."
}}

Allowed labels:

defeater_present:
- yes: The new information epistemically affects the agent's initial support for p.
- no: The new information does not epistemically affect the agent's initial support for p.

defeater_type:
- none_placebo: No real defeater is present; the new information is irrelevant, already accounted for, or has no epistemic effect on the initial support for p.
- rebutting_defeater: The new information gives evidence against p or evidence for not-p.
- undercutting_defeater: The new information weakens the connection between the agent's original reason or evidence and p, without itself directly supporting not-p.
- higher_order_defeater: The new information gives the agent reason to doubt their own reliability, competence, reasoning, perception, memory, or evidence-handling in this case.

defeater_strength:
- none: The new information has no impact on the initial epistemic support for p.
- weak: The new information reduces support for p, but p remains epistemically better supported than not-p.
- moderate: The new information reduces support for p enough that p and not-p are equally supported, or the agent's reasons no longer favor either side.
- strong: The new information makes not-p epistemically better supported than p.

support_relation:
- no_impact: The new information has no effect on the initial epistemic support for p.
- target_better_supported: After considering the new information, p remains epistemically better supported than not-p.
- equal_support: After considering the new information, p and not-p are equally supported, or the agent's reasons favor neither.
- negation_better_supported: After considering the new information, not-p is epistemically better supported than p.

belief_revision:
- maintain_target_belief: The agent should continue believing p.
- suspend_judgment: The agent should neither believe p nor believe not-p because the available reasons do not favor either side.
- believe_negation: The agent should believe not-p.

Important:
- Evaluate each output field only with respect to the target proposition provided.
- If defeater_present is no, set defeater_type to none_placebo.
- Return JSON only. Do not include markdown or extra text. The brief_explanation field should be one concise sentence explaining the classification.

Scenario:
{scenario}

Target proposition:
{target_proposition}

Question:
{question}"""

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
    family_templates = {
        "belief_truth_knowledge": BELIEF_TRUTH_KNOWLEDGE_PROMPT,
        "acceptance_and_belief": ACCEPTANCE_AND_BELIEF_PROMPT,
        "justification": JUSTIFICATION_PROMPT,
    }
    if case.module == "belief_acceptance_knowledge" and case.schema_family in family_templates:
        return family_templates[case.schema_family].format(
            scenario=case.scenario,
            target_proposition=case.target_proposition,
            question=case.question,
        )
    if case.module == "epistemic_luck":
        return EPISTEMIC_LUCK_PROMPT.format(
            scenario=case.scenario,
            target_proposition=case.target_proposition,
            question=case.question,
        )
    if case.module == "rational_reasoning" and case.schema_family == "deduction":
        return RATIONAL_REASONING_PROMPT.format(
            scenario=case.scenario,
            target_proposition=case.target_proposition,
            question=case.question,
        )
    if case.module == "defeaters":
        return DEFEATERS_PROMPT.format(
            scenario=case.scenario,
            target_proposition=case.target_proposition,
            question=case.question,
        )

    field_lines = [_field_spec(label, value) for label, value in case.expected.items()]
    field_lines.append('  "brief_explanation": one sentence, at most 25 words')
    fields_block = ",\n".join(field_lines)

    return (
        f"Scenario:\n{case.scenario}\n\n"
        f"Target proposition: {json.dumps(case.target_proposition)}\n\n"
        f"Question: {case.question}\n\n"
        "Answer with a JSON object containing exactly these fields, choosing "
        "each value only from the options shown:\n"
        "{\n"
        f"{fields_block}\n"
        "}\n\n"
        f"{RESPONSE_RULES}"
    )
