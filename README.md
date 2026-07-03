# Epistemically

Practical evaluation of LLM behavior under epistemic norms.

**Epistemically** is a practical LLM evaluation framework for testing whether language model outputs manage epistemic status responsibly. It evaluates model behavior on cases involving belief, truth, justification, knowledge, deduction, defeaters, and epistemic luck.

The project is inspired by epistemology, but it makes **no claim that LLMs literally believe, know, or possess conscious doxastic states**. Cases describe agents in scenarios, and the model is scored on whether its structured judgments about those agents match expected labels.

## What it evaluates

The first version focuses on five modules:

| Module | Probes |
| --- | --- |
| `belief_truth_knowledge` | Separating an agent's belief from truth, justification, and knowledge |
| `gettier_luck` | Justified true belief that falls short of knowledge because of epistemic luck |
| `deduction_rationality` | Validity, entailment recognition, and rational consistency |
| `defeaters` | Justification updates under undercutting, rebutting, source-reliability, higher-order, and dependency defeaters |
| `induction_updating` | Inductive inference and evidence updating; no seed cases yet |

## Why this exists

Many LLM evaluation tools focus on factuality, hallucination, task completion, preference ranking, or general instruction following. Epistemically focuses on a narrower question:

> Can a model responsibly track the epistemic status of a claim?

This includes cases where a proposition is true but not known, believed but false, justified but false, validly inferred from false premises, defeated by new evidence, or true only because of epistemic luck.

## Evaluation approach

Each evaluation item is an epistemic case with structured expected labels. Models are asked to return constrained JSON. Scoring is mostly deterministic exact-label comparison, with component-level partial credit.

Example labels include:

- `belief_status`
- `truth_status`
- `justification_status`
- `knowledge_status`
- `epistemic_status`
- `failure_mode`
- `defeater_type`
- `updated_status`
- `confidence_direction`

## Statistics

Epistemically reports:

- mean score by model
- mean score by module
- bootstrap confidence intervals
- paired bootstrap model comparisons
- error taxonomy counts
- failure examples

The final score is a behavioral evaluation score, not a measure of literal machine knowledge.

## Quickstart

```bash
# 1. Install
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -e .

# 2. Configure
copy .env.example .env        # Windows
# cp .env.example .env        # Mac/Linux