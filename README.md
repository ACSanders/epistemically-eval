# Epistemically

**An epistemic AI lab for evaluating how language models handle epistemic luck, belief, truth, knowledge, defeaters, and rational inference.**

🌐 **Live demo:** [epistemically.com](https://epistemically.com)

Epistemically is a work-in-progress LLM evaluation framework and Streamlit dashboard inspired by epistemology.

Most benchmarks ask whether a model gets the answer right. Epistemically asks a more specific question:

> Does the model track the epistemic status of a claim?

That means evaluating whether model outputs correctly distinguish belief, truth, justification, knowledge, rational inference, defeaters, and epistemic luck in controlled philosophical scenarios.

Epistemically does **not** claim that LLMs literally believe, know, understand, or possess epistemic agency. It behaviorally evaluates model outputs under operational epistemic rubrics. When this project says a model recognizes knowledge, justification, or epistemic luck, it means the model produced the expected structured classification for a case involving those concepts.

---

## Why this project exists

A model can get a claim right while still mishandling the epistemic status of that claim.

For example:

- A belief can be true without being knowledge.
- A belief can be justified but false.
- A belief can be true and justified but still fail to be knowledge because of luck.
- A belief can be rationally defeated by new evidence.
- A conclusion can validly follow from premises even if the premises are false.
- An agent can accept a claim for practical reasons without believing it.

Epistemically is designed to make these distinctions visible.

The goal is not just an overall score. The goal is an **epistemic fingerprint** for each model: where it succeeds, where it fails, and what kind of epistemic mistakes it tends to make.

---

## Current benchmark

The current benchmark includes:

- **150 hand-written cases**
- **4 active epistemology modules**
- **6 evaluated models**
- **3 model providers**
- Structured JSON model outputs
- Exact-label component scoring
- Weighted field-level scores
- Bootstrap confidence intervals
- Paired model comparison
- Failure gallery
- Case explorer
- Model profile views
- Module and schema-family heatmaps
- Streamlit dashboard with a dark visual identity

Current evaluated models:

| Provider | Model |
|---|---|
| OpenAI | `gpt-4o-mini` |
| OpenAI | `gpt-5-mini` |
| Anthropic | `claude-haiku-4-5` |
| Anthropic | `claude-sonnet-5` |
| Anthropic | `claude-opus-4-8` |
| Google | `gemini-2.5-pro` |

Current leaderboard from the committed result files:

| Model | Overall score |
|---|---:|
| `claude-opus-4-8` | 0.978 |
| `gpt-5-mini` | 0.960 |
| `gemini-2.5-pro` | 0.953 |
| `claude-sonnet-5` | 0.951 |
| `claude-haiku-4-5` | 0.923 |
| `gpt-4o-mini` | 0.800 |

These results are useful as a live research prototype and public demo. They should not be treated as final leaderboard claims. The benchmark is still growing, and several modules need more cases, variants, and review.

---

## Flagship focus: epistemic luck

The flagship module is **epistemic luck**.

Classic Gettier-style cases show that justified true belief is not always knowledge. A subject can believe a proposition, have justification, and be correct, while still failing to know because the truth of the belief is too lucky.

Epistemically brings that distinction into LLM evaluation.

The core question is:

> Can a model distinguish knowledge from lucky true belief?

This matters because many evaluations focus on correctness. But correctness alone is not enough. In epistemic-luck cases, a model may classify an agent as knowing simply because the target proposition is true and the agent has some support. That is the exact failure the module is designed to expose.

The current `epistemic_luck` module includes 30 cases across four schema families:

| Schema family | Purpose |
|---|---|
| `knowledge_control` | Ordinary knowledge cases with no relevant epistemic luck |
| `lucky_guess` | True beliefs formed without adequate justification |
| `intervening_luck` | Gettier-style cases where the truth is lucky because something goes wrong between the subject's reason and the target fact |
| `environmental_luck` | Cases where the subject forms a true belief in an unsafe epistemic environment |

Example expected output:

```json
{
  "justification_status": "justified",
  "knowledge_status": "does_not_know",
  "luck_status": "epistemic_luck_present",
  "luck_type": "intervening_luck"
}
```

Early results show useful model fingerprints. For example, `claude-opus-4-8` solved the epistemic-luck module perfectly, while `gpt-4o-mini` often detected that luck was present but collapsed justified lucky true belief into lucky guessing. `claude-haiku-4-5` showed a different failure pattern, often granting knowledge in intervening-luck cases where knowledge should be denied.

Those are the kinds of structured epistemic differences Epistemically is built to surface.

---

## Active modules

### 1. Belief, acceptance, and knowledge

Module key: `belief_acceptance_knowledge`

This module tests whether models distinguish:

- belief from truth
- belief from pragmatic acceptance
- truth from knowledge
- epistemic justification from practical motivation
- justified belief from unjustified belief
- determinate knowledge from underdetermined cases

Current schema families:

- `belief_truth_knowledge`
- `acceptance_and_belief`
- `justification`

### 2. Defeaters

Module key: `defeaters`

This module tests whether models update appropriately when new information affects an existing belief.

It focuses on belief revision behavior rather than over-weighting fine-grained taxonomy. Cases include:

- rebutting defeaters
- undercutting defeaters
- higher-order defeaters
- irrelevant or placebo information

Current schema family:

- `rebuttal_and_undercut`

### 3. Rational reasoning

Module key: `rational_reasoning`

This module tests whether models recognize deductive patterns, logical status, and rational constraints.

It includes cases involving:

- direct contradiction
- joint inconsistency
- consistent belief sets
- modus ponens
- modus tollens
- affirming the consequent
- denying the antecedent
- hypothetical syllogism
- disjunctive syllogism
- constructive dilemma
- simplification
- addition
- categorical syllogism
- non sequitur
- equivocation

Current schema family:

- `deduction`

### 4. Epistemic luck

Module key: `epistemic_luck`

This module tests whether models distinguish ordinary knowledge from lucky true belief.

It includes:

- knowledge controls
- lucky guesses
- intervening luck
- environmental luck

Current schema families:

- `knowledge_control`
- `lucky_guess`
- `intervening_luck`
- `environmental_luck`

---

## What makes Epistemically different

Most LLM evaluation tools focus on factuality, hallucination, task success, preference ranking, or general instruction following.

Those are important. But they do not fully capture whether a model can track the epistemic status of a claim.

Epistemically asks questions like:

- Does the model distinguish what an agent believes from what is true?
- Does it recognize that knowledge requires truth?
- Does it distinguish justified belief from knowledge?
- Does it avoid treating lucky true belief as knowledge?
- Does it detect when a belief is defeated by new evidence?
- Does it distinguish valid inference from invalid inference?
- Does it avoid over-updating when new information is irrelevant?
- Does it separate epistemic reasons from practical reasons?
- Does it handle underdetermined cases without overcommitting?

The dashboard is built around those failure patterns. Two models can have similar overall scores while failing in very different ways.

---

## Dashboard

The Streamlit dashboard is designed as an epistemic evaluation lab interface.

Current views:

### Overview

High-level model performance:

- overall score
- cases evaluated
- failure count
- strongest and weakest module
- module performance heatmap
- schema-family heatmap
- bootstrap confidence intervals

### Model Profile

A model-specific view of strengths and weaknesses:

- module profile
- module scores
- schema-family performance
- field-level behavior
- interpretive summaries

### Model Comparison

Pairwise comparison between any two evaluated models:

- shared solved cases
- improved cases
- regressed cases
- persistently hard cases
- score deltas
- paired bootstrap comparison

This is where Epistemically becomes most useful. It can show not just which model scores higher, but how two models fail differently.

### Failure Gallery

A card-based review of imperfect cases:

- scenario
- target proposition
- expected labels
- model labels
- per-field correctness
- model explanation
- score

### Case Explorer

A detailed case-level interface for inspecting individual model outputs.

### Methodology

The methodology section is available in the app footer. It summarizes what the benchmark evaluates, how exact-label scoring works, what the confidence intervals mean, and what limitations apply.

---

## Methodology

Each evaluation item is a short epistemic case. A case includes:

- `id`
- `module`
- `schema_family`
- `scenario`
- `target_proposition`
- `question`
- `expected`
- `scoring_weights`
- `difficulty`
- `notes`

The model is asked to return structured JSON using only allowed labels. The evaluator compares model labels against expected labels field by field.

The scoring rule is:

```text
case score = weighted correct fields / total weighted fields
```

This makes scoring transparent and auditable. Every point can be traced to a specific field on a specific case.

Epistemically currently uses exact-label scoring. This is strict, but it avoids relying on another model as a judge. The tradeoff is that near misses do not receive partial credit. Model explanations are collected when available, but the `brief_explanation` field is unscored.

Bootstrap confidence intervals are used to summarize uncertainty over the current case set. Pairwise model comparisons use paired bootstrap differences across the same cases.

---

## Current result highlights

The current six-model comparison already surfaces several useful patterns:

- `claude-opus-4-8` currently leads overall and is the first model in the benchmark to solve the epistemic-luck module perfectly.
- `gpt-5-mini`, `gemini-2.5-pro`, and `claude-sonnet-5` are close overall but show different failure profiles.
- All Claude models performed perfectly on the defeaters module in the current run.
- `gpt-4o-mini` and `claude-haiku-4-5` fail intervening-luck cases in different ways.
- `gemini-2.5-pro` is near-perfect on epistemic luck but shows a distinctive two-direction confusion on reason-type labels.
- Several indeterminate knowledge cases remain difficult across all evaluated models.

These should be treated as diagnostic findings from the current case set, not as final claims about model capability in general.

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

Install dependencies:

```bash
pip install -r requirements.txt
```

Or install the project in editable mode:

```bash
pip install -e .
```

Launch the dashboard:

```bash
streamlit run app.py
```

The dashboard runs from committed CSV files in `data/results/`. You do not need API keys to view the dashboard.

---

## Running evaluations

API keys are only needed if you want to run new model evaluations.

Create a local `.env` file from the template:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Add only the keys you need:

```text
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here
```

Do not commit `.env`. It is local only.

Validate cases:

```bash
python scripts/validate_cases.py data/cases/user_cases_draft.jsonl
```

Run an OpenAI model:

```bash
python scripts/run_eval.py --cases data/cases/user_cases_draft.jsonl --model gpt-5-mini --output data/results/user_cases_results_gpt-5-mini.csv
```

Run an Anthropic model:

```bash
python scripts/run_eval.py --cases data/cases/user_cases_draft.jsonl --model claude-opus-4-8 --output data/results/user_cases_results_claude-opus-4-8.csv
```

Run a Gemini model:

```bash
python scripts/run_eval.py --cases data/cases/user_cases_draft.jsonl --model gemini-2.5-pro --output data/results/user_cases_results_gemini-2.5-pro.csv
```

Run a small smoke test:

```bash
python scripts/run_eval.py --cases data/cases/user_cases_draft.jsonl --model gemini-2.5-pro --limit 2 --output data/results/test_gemini_smoke.csv
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

The public dashboard runs from committed result CSVs and does not make API calls. No API keys are required to view the deployed app.

---

## Repository structure

```text
epistemically-eval/
├── app.py
├── pyproject.toml
├── README.md
├── requirements.txt
├── data/
│   ├── cases/
│   │   ├── sample_cases.jsonl
│   │   ├── user_cases_draft.jsonl
│   │   └── user_cases_template.md
│   └── results/
│       ├── user_cases_results_gpt-4o-mini.csv
│       ├── user_cases_results_gpt-5-mini.csv
│       ├── user_cases_results_claude-haiku-4-5.csv
│       ├── user_cases_results_claude-sonnet-5.csv
│       ├── user_cases_results_claude-opus-4-8.csv
│       ├── user_cases_results_gemini-2.5-pro.csv
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
            ├── common.py
            ├── openai_runner.py
            ├── anthropic_runner.py
            └── gemini_runner.py
```

---

## Current limitations

Epistemically is still early and intentionally evolving.

Current limitations:

- The benchmark has 150 cases, but several schema families still need more examples.
- Cases are hand-written and should continue to receive philosophical and empirical review.
- Expected labels follow mainstream epistemological concepts, but some cases, especially environmental luck and fake-barn-style cases, remain philosophically contestable.
- Exact-label scoring is transparent but can be brittle.
- Current results are single runs at temperature 0 and do not measure sampling variance.
- The benchmark is not yet large enough for strong leaderboard-style claims.
- Some result files include row-level parsing failures, which are scored as zero according to the benchmark policy.

---

## Roadmap

Near-term priorities:

- Expand the benchmark to 250 to 500 reviewed cases.
- Add more epistemic-luck variants while preserving philosophical clarity.
- Expand social epistemology modules, especially testimony and disagreement.
- Add induction and evidence-updating cases.
- Add more difficult defeater variants.
- Add repeated-run stability checks.
- Add case difficulty estimates.
- Improve documentation and related-work notes.
- Add more provider and open-weight model support where practical.

Longer-term ideas:

- Human review workflow for gold labels.
- Cross-prompt robustness testing.
- Explanation-quality analysis.
- Calibration and uncertainty modules.
- Hierarchical or Bayesian score estimates.
- Active generation of hard cases with manual review.
- Public comparison reports.
- A future epistemic theory profile module.

The future epistemic theory profile would not claim that a model literally holds a philosophical view. It would behaviorally profile whether a model's outputs resemble patterns associated with views such as reliabilism, evidentialism, internalism, externalism, contextualism, virtue epistemology, pragmatic encroachment, or knowledge-first epistemology.

---

## Related work

Epistemically is related to work on:

- LLM factuality
- hallucination evaluation
- truthfulness benchmarks
- theory-of-mind benchmarks
- belief revision
- defeasible reasoning
- epistemic calibration
- Gettier-style epistemic luck
- structured model evaluation frameworks

The goal is not to replace those projects. The goal is to build a practical, inspectable evaluation suite organized around epistemological case types, behavioral model outputs, component-level scoring, uncertainty estimates, and model profiles.

See also:

- `docs/methodology.md`
- `docs/related_work.md`

---

## License

MIT License.
