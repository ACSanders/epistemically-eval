# Epistemically.

**An epistemic AI lab for evaluating how language models track belief, truth, knowledge, inference, defeaters, and luck.**

🌐 **Live demo:** [epistemically.com](https://epistemically.com)

Epistemically is a work-in-progress LLM evaluation framework and Streamlit dashboard inspired by epistemology. It tests whether model outputs can correctly classify the epistemic status of agents in structured cases: what they believe, whether the target proposition is true, whether the belief is justified, whether the subject knows, whether an inference is valid, and whether new evidence should revise or defeat a belief.

The project is designed as a practical AI evaluation lab, not a philosophy dissertation. The goal is to build a cutting-edge, inspectable, statistically grounded evaluation tool for model behavior under epistemic norms.

Epistemically does **not** claim that LLMs literally believe, know, understand, or possess conscious doxastic states. It evaluates model outputs behaviorally.

---

## Why Epistemically exists

Most LLM evaluation tools focus on factuality, hallucination, task completion, preference ranking, benchmark accuracy, or general instruction following.

Those are important, but they do not fully capture whether a model can responsibly track the epistemic status of a claim.

Epistemically asks narrower and more philosophically structured questions:

- Does the model distinguish **belief** from **truth**?
- Does it distinguish **true belief** from **knowledge**?
- Does it recognize when justification is present, absent, or defective?
- Does it understand that knowledge is factive?
- Does it recognize Gettier-style epistemic luck?
- Does it distinguish valid from invalid inference?
- Does it update appropriately when new evidence defeats or weakens a belief?
- Does it avoid over-updating to irrelevant information?

The core idea is simple:

> A model can answer a question correctly while still mishandling the epistemic status of the answer.

Epistemically is designed to make those distinctions visible.

---

## Current v0 modules

Epistemically currently includes 24 seed cases across four active modules, with a fifth planned module.

| Module | What it tests |
| --- | --- |
| `belief_truth_knowledge` | Whether a model separates what an agent believes, what is true, whether the belief is justified, and whether the agent knows. |
| `gettier_luck` | Whether a model distinguishes knowledge from lucky true belief in Gettier-style cases. |
| `deduction_rationality` | Whether a model recognizes valid inference forms, invalid inference forms, contradiction, and rational consistency requirements. |
| `defeaters` | Whether a model updates appropriately when new evidence weakens, rebuts, or fails to affect a belief. |
| `induction_updating` | Planned module for inductive reasoning, probabilistic support, and evidence updating. |

---

## What the current prototype does

The current prototype includes:

- 24 hand-written epistemic evaluation cases
- OpenAI runner for model evaluation
- Structured JSON-only model outputs
- Exact-label component scoring
- Weighted field-level scores
- Bootstrap confidence intervals
- Module-level score summaries
- Failure gallery
- Case explorer
- Radar chart for epistemic module profile
- Module × schema-family heatmap
- Dark Streamlit dashboard with orange/coral visual identity

The current seed result file evaluates `gpt-4o-mini` on the 24-case draft benchmark. This is a prototype result, not a final benchmark claim.

---

## Methodology

Each evaluation item is an epistemic case. A case includes:

- `id`
- `module`
- `schema_family`
- `scenario`
- `target_proposition`
- `question`
- `expected` structured labels
- `scoring_weights`
- `difficulty`
- `notes`

The model is asked to return structured JSON using only allowed labels. The evaluator compares model labels against expected labels field by field.

Example:

```json
{
  "belief_status": "believes",
  "truth_status": "true",
  "justification_status": "unjustified",
  "knowledge_status": "does_not_know",
  "epistemic_status": "true_belief"
}
```

The scoring system is intentionally simple and inspectable:

```text
case score = weighted correct fields / total weighted fields
```

This allows the dashboard to show not just whether a model passed a case, but exactly which epistemic component it handled correctly or incorrectly.

---

## Scoring philosophy

Epistemically currently uses **exact-label scoring**.

That means a model must output the exact expected label string, such as:

```text
does_not_know
false_belief
lucky_true_belief
undercutting_defeater
```

This may seem strict, but it has an important advantage: it keeps the scoring transparent, reproducible, and independent of an LLM judge.

The current approach avoids using another model to decide whether an answer is close enough. Instead, it creates a clear behavioral evaluation:

> Did the model select the expected epistemic classification under the provided rubric?

Future versions may add secondary semantic or explanation-quality scoring, but exact component scoring remains the foundation.

---

## Statistics

Epistemically reports:

- Mean score by model
- Mean score by module
- Mean score by schema family
- Bootstrap confidence intervals
- Field-level correctness
- Failure counts
- Failure examples
- Module profile radar charts
- Module × schema-family heatmaps

The bootstrap intervals are intended to show uncertainty over the current case set. They should not be overinterpreted as final population-level claims, especially while the benchmark is still small.

As the dataset grows, Epistemically will support stronger model comparisons, including paired bootstrap differences across models evaluated on the same cases.

---

## Dashboard

The Streamlit dashboard is designed as an epistemic AI lab interface.

Current views include:

### Overview

High-level model performance:

- Overall epistemic score
- Cases evaluated
- Failure count
- Strongest module
- Weakest module
- Points earned / possible
- Module score chart with confidence intervals

### Module Profile

A compact view of the model’s epistemic strengths and weaknesses:

- Radar chart across modules
- Module × schema-family heatmap
- Interpretive summary

### Failure Gallery

A card-based review of imperfect cases, showing:

- Scenario
- Target proposition
- Expected labels
- Model labels
- Per-field correctness
- Model explanation
- Score

This is where the evaluation becomes most useful. Many failures are not just wrong answers, but specific epistemic confusions, such as treating a lucky true belief as a false belief or confusing an invalid inference with a false conclusion.

### Case Explorer

A detailed case-level interface for inspecting any result row.

### Methodology

A concise explanation of what the tool measures, how scoring works, and what the current limitations are.

---

## Current design decisions

### Behavioral framing

Epistemically does not attribute literal mental states to models.

When the dashboard says a model tracks belief or recognizes knowledge, it means:

> The model produced the expected structured output for a case involving an agent’s belief, truth, justification, or knowledge.

This is behavioral evaluation, not a metaphysical claim.

### Defeater module

The defeater module currently prioritizes **belief revision** over fine-grained taxonomy.

For v0, the mainstream defeater labels are:

- `none_placebo`
- `rebutting_defeater`
- `undercutting_defeater`
- `higher_order_defeater`

The model may output `defeater_type`, but this field is currently diagnostic rather than part of the primary score. The primary score focuses on whether the model updates appropriately:

- retain belief
- reduce confidence
- believe not-p
- leave confidence unchanged for irrelevant evidence

This avoids over-penalizing reasonable taxonomy disputes while still testing whether the model responds appropriately to new evidence.

### Deduction module

The deduction module scores inference-related fields such as:

- `inference_type`
- `validity`
- `conclusion_follows`
- `rational_requirement`
- `contradiction_present`
- `consistency_status`

It does not currently score a broad `epistemic_status` summary field for deduction cases, because that created avoidable ambiguity between knowledge, validity, and rational commitment.

---

## Example failure patterns

The current prototype already surfaces interesting model behavior.

Examples of failure types include:

- Correctly identifying belief, truth, defective justification, and epistemic luck, while still summarizing the case as `false_belief` instead of `lucky_true_belief`.
- Recognizing that an agent’s commitments are inconsistent while misclassifying a modus ponens inference as invalid.
- Correctly identifying that a subject does not believe a true proposition, while still summarizing the case as a false belief.

These are exactly the kinds of structured epistemic confusions the project is designed to expose.

---

## Quickstart

Clone the repo:

```bash
git clone https://github.com/ACSanders/epistemically-eval.git
cd epistemically-eval
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Mac/Linux:

```bash
source .venv/bin/activate
```

Install the project:

```bash
pip install -e .
```

Copy the environment template:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Add an OpenAI API key to `.env` only if you want to run new API evaluations:

```text
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

The dashboard can run from the committed result CSV without making API calls.

Validate cases:

```bash
python scripts/validate_cases.py
python scripts/validate_cases.py data/cases/user_cases_draft.jsonl
```

Run the evaluation:

```bash
python scripts/run_eval.py --cases data/cases/user_cases_draft.jsonl --output data/results/user_cases_results.csv
```

Launch the dashboard:

```bash
streamlit run app.py
```

---

## Render deployment

The app can be deployed as a Streamlit web service.

Render build command:

```bash
pip install -r requirements.txt
```

Render start command:

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

The dashboard runs from the committed CSV results in `data/results/` and makes
no API calls, so no secrets are required to view it. `OPENAI_API_KEY` is only
needed for future live evaluation runs (`scripts/run_eval.py`), not for
viewing the current dashboard.

---

## Repository structure

```text
epistemically-eval/
├── app.py
├── pyproject.toml
├── README.md
├── data/
│   ├── cases/
│   │   ├── sample_cases.jsonl
│   │   ├── user_cases_draft.jsonl
│   │   └── user_cases_template.md
│   └── results/
│       └── user_cases_results.csv
├── docs/
│   ├── methodology.md
│   └── related_work.md
├── scripts/
│   ├── run_eval.py
│   └── validate_cases.py
└── src/
    └── epistemically/
        ├── analysis.py
        ├── app_utils.py
        ├── bootstrap.py
        ├── dataset.py
        ├── labels.py
        ├── prompts.py
        ├── schemas.py
        ├── scoring.py
        └── runners/
            └── openai_runner.py
```

---

## Current limitations

Epistemically is early and intentionally evolving.

Current limitations:

- The seed benchmark is small.
- Cases are hand-written and need further review.
- Some schema families need more examples.
- Defeater cases are currently too easy.
- The current runner supports OpenAI only.
- Scores depend on the quality and clarity of the gold labels.
- Exact-label scoring is transparent but can be brittle.
- The benchmark is not yet large enough for strong leaderboard-style claims.

This project should currently be understood as a working prototype and research/product direction, not a finished benchmark.

---

## Roadmap

### v0 — Working prototype

Current state:

- OpenAI runner
- 24 seed cases
- Exact-label scoring
- Bootstrap confidence intervals
- Streamlit dashboard
- Dark UI
- Failure gallery
- Case explorer
- Module radar chart
- Module × schema-family heatmap

### v0.1 — Better benchmark quality

Near-term improvements:

- Expand to 50–100 curated cases
- Improve gold-label consistency
- Add paraphrase variants
- Add case difficulty tags
- Add stronger schema-family coverage
- Add clearer failure taxonomies
- Add more challenging defeater cases
- Add robustness checks across repeated model calls

### MVP — Public demo

Deployment-focused improvements:

- Deploy public dashboard
- Connect `epistemically.com`
- Add polished documentation
- Add screenshots and demo GIFs
- Include one or more stable model result files
- Add methodology page in the dashboard
- Improve mobile responsiveness

### v1 — Multi-model evaluation

Model-comparison work:

- Add Anthropic runner
- Add Gemini runner
- Add local/open-weight model support if practical
- Add model comparison dashboard
- Add paired bootstrap difference estimates
- Add model × module heatmaps
- Add repeated-run stability metrics
- Add exportable reports

### v2 — Dataset expansion and reliability

Benchmark-quality work:

- Expand to 250–500 reviewed cases
- Add generated variants with manual review
- Add schema-family bootstrapping
- Estimate case difficulty
- Track inter-reviewer agreement for gold labels
- Add reliability and stability analysis
- Separate primary scores from diagnostic fields
- Improve partial-credit options without relying on LLM judges

### v3 — Epistemic Theory Profile

A future module may evaluate how a model’s structured responses pattern across classic epistemological questions.

This would not claim that a model literally “is a reliabilist” or “believes contextualism.” Instead, it would behaviorally profile outputs as resembling epistemological positions under controlled prompts.

Potential theory families:

- Reliabilism
- Evidentialism
- Internalism
- Externalism
- Foundationalism
- Coherentism
- Virtue epistemology
- Contextualism
- Knowledge-first epistemology
- Pragmatic encroachment
- Safety and sensitivity theories
- Testimony and social epistemology
- Assertion norms

This module should separate two tasks:

1. **View classification**  
   Can the model correctly identify a philosophical view from a structured description?

2. **Behavioral profile inference**  
   Across structured answers, what epistemological patterns do the model’s outputs resemble?

Possible visualizations:

- Epistemic compass
- Theory radar chart
- Model profile card
- Disagreement/instability map
- Theory-family heatmap

The framing should remain careful:

> The model’s outputs exhibit a pattern resembling a view, not the model literally holds that view.

---

## Longer-term ideas

Potential future directions:

- Explanation-quality scoring
- Calibration curves
- Bayesian or hierarchical score estimates
- Active generation of hard cases
- Human review interface for gold labels
- Model self-consistency checks
- Cross-prompt robustness testing
- Public comparison reports
- Epistemic error taxonomy
- Leaderboard only after benchmark quality improves

---

## Related work

Epistemically is related to work on:

- LLM factuality
- Hallucination evaluation
- Truthfulness benchmarks
- Theory-of-mind benchmarks
- Belief revision
- Defeasible reasoning
- Epistemic calibration
- Gettier-style epistemic luck
- Structured model evaluation frameworks

The goal is not to replace those projects. The goal is to build a practical, inspectable evaluation suite organized around epistemological case types and component-level scoring.

See:

- `docs/methodology.md`
- `docs/related_work.md`

---

## License

MIT License.
