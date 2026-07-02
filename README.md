# Epistemically

**Epistemically** is a practical LLM evaluation framework for testing whether language models manage epistemic status responsibly.

It evaluates model behavior on cases involving belief, knowledge, truth, justification, deduction, defeaters, and epistemic luck. The goal is not to claim that LLMs literally have beliefs, knowledge, or conscious doxastic states. Instead, Epistemically treats model outputs as behavioral evidence and asks whether models classify epistemic situations in normatively appropriate ways.

## What it evaluates

The first version focuses on four core modules:

1. **Belief / Knowledge / Fact**
   Tests whether models distinguish belief from truth, truth from knowledge, false belief from true belief, and knowledge from mere assertion.

2. **Deduction / Rationality**
   Tests whether models recognize valid and invalid inference forms, consistency requirements, validity versus soundness, and rational closure under obvious entailment.

3. **Defeaters**
   Tests whether models update appropriately when new information undermines a claim, a reason, a source, or a dependency. This includes rebutting defeaters, undercutting defeaters, source-reliability defeaters, higher-order defeaters, and placebo/noise refuters.

4. **Gettier / Epistemic Luck**
   Tests whether models distinguish knowledge from lucky true belief by classifying belief, truth, justification, knowledge, and failure mode.

## Why this exists

Many LLM evaluation tools focus on factuality, hallucination, task completion, preference ranking, or general instruction following. Epistemically focuses on a narrower question:

> Can a model responsibly track the epistemic status of a claim?

This includes cases where a statement is true but not known, believed but false, justified but defeated, validly inferred from false premises, or true only because of epistemic luck.

## What this project is not

Epistemically does **not** claim that LLMs literally know things, believe things, or possess conscious epistemic states.

It is a model-behavior evaluation suite inspired by epistemology. The model's classifications, confidence, and explanations are evaluated as outputs under epistemic norms.

## Evaluation approach

Each evaluation item is an epistemic case with structured expected labels. Models are asked to return constrained JSON. Scoring is mostly deterministic exact-label comparison, with component-level partial credit.

Example labels include:

* `belief_status`
* `truth_status`
* `justification_status`
* `knowledge_status`
* `epistemic_status`
* `failure_mode`
* `defeater_type`
* `updated_status`
* `confidence_direction`

## Statistics

Epistemically reports:

* mean score by model
* mean score by module
* bootstrap confidence intervals
* paired bootstrap model comparisons
* error taxonomy counts
* failure examples

The final score is a behavioral eval score, not a measure of literal machine knowledge.

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows PowerShell

pip install -e .
cp .env.example .env
```

Add your API key to `.env`:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=your_model_here
```

Validate sample cases:

```bash
python scripts/validate_cases.py
```

Run the sample evaluation:

```bash
python scripts/run_eval.py
```

Launch the dashboard:

```bash
streamlit run app.py
```

## Related work

Epistemically is related to prior work on LLM evaluation, belief/knowledge benchmarks, belief revision, defeasible reasoning, epistemic calibration, and benchmarks such as EpiK-Eval. The goal is not to replace those projects, but to create a practical, inspectable evaluation suite organized around epistemological case types and component-level scoring.

## Roadmap

* v0: sample cases, OpenAI runner, exact-label scoring, Streamlit dashboard
* v0.1: 50–100 curated cases
* MVP: bootstrap confidence intervals, module scores, failure gallery
* v1: 250–500 reviewed cases, paraphrase robustness, stability checks
* Later: Anthropic/Gemini adapters, model profile clustering, calibration curves, active hard-case generation
