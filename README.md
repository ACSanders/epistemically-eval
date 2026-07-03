# Epistemically

**An AI epistemology lab for evaluating how language models handle belief, truth, knowledge, inference, defeaters, and epistemic luck.**

🌐 **Live demo:** [epistemically.com](https://epistemically.com)

Epistemically is a work-in-progress LLM evaluation framework and Streamlit dashboard inspired by epistemology. It is designed to test whether language models can correctly track the epistemic status of claims in structured cases: what an agent believes, whether the target proposition is true, whether the belief is justified, whether the agent knows, whether an inference is valid, whether a belief is defeated by new evidence, and whether a true belief falls short of knowledge because of epistemic luck.

This project is an applied AI evaluation lab, not a philosophy dissertation. The goal is to build a practical, inspectable, statistically grounded tool for studying model behavior under epistemic norms.

Epistemically does **not** claim that LLMs literally believe, know, understand, or possess conscious mental states. The project evaluates model outputs behaviorally. When Epistemically says a model recognizes knowledge, belief, justification, or epistemic luck, it means the model produced the expected structured classification for a case involving those concepts.

The long-term vision is to make Epistemically a distinctive evaluation suite for AI systems: one that goes beyond factuality and accuracy to ask whether models can represent the difference between a correct answer, a justified answer, a lucky answer, a defeated answer, and a known answer.

---

## Flagship focus: epistemic luck and Gettier-style evaluation

The flagship direction for Epistemically is the evaluation of **epistemic luck**, especially Gettier-style cases.

Classic Gettier cases show that justified true belief is not always knowledge. A person can believe something, have justification, and even be correct, while still failing to know because the truth of the belief is too lucky. This distinction is central to epistemology, but it is not usually front and center in practical LLM evaluation.

Epistemically brings that distinction into AI evaluation.

The core question is:

> Can a language model distinguish knowledge from lucky true belief?

This matters because many model evaluations focus on whether an answer is correct. But correctness alone is not enough. A model may classify a case as knowledge simply because the agent has a true belief with some justification. In Gettier-style cases, that is exactly the mistake.

Epistemically is designed to expose that kind of failure.

A model should be able to separate:

* belief from truth
* truth from justification
* justification from knowledge
* true belief from lucky true belief
* lucky true belief from knowledge
* valid inference from knowledge transmission
* evidence from pragmatic acceptance
* relevant defeaters from irrelevant information

The project does not claim to be the first work to connect epistemology and AI. There is related work on LLM factuality, hallucination, truthfulness, defeasible reasoning, belief revision, theory of mind, and epistemic evaluation. Epistemically aims to contribute something more specific and applied: a hands-on AI epistemology lab that uses structured epistemic cases, component-level labels, scoring, uncertainty estimates, model profiles, and an interactive dashboard to evaluate how LLMs handle epistemic distinctions.

The key idea is simple:

> A model can get the answer right while still mishandling the epistemic status of the answer.

Epistemically is built to make those hidden failures visible.

---

## What makes Epistemically different

Most LLM evaluation tools focus on factuality, hallucination, benchmark accuracy, task completion, preference ranking, or general instruction following.

Those are important, but they do not fully capture whether a model can responsibly track the epistemic status of a claim.

Epistemically asks a different set of questions:

* Does the model distinguish what an agent believes from what is true?
* Does it understand that knowledge requires truth?
* Does it distinguish justified belief from knowledge?
* Does it recognize when justification is defective?
* Does it identify Gettier-style epistemic luck?
* Does it avoid treating lucky true belief as knowledge?
* Does it distinguish valid from invalid inference?
* Does it update appropriately when new evidence defeats a belief?
* Does it avoid over-updating when information is irrelevant?
* Does it produce stable epistemic classifications across related cases?

The goal is not just to produce an overall score. The goal is to create an **epistemic fingerprint** for each model.

Two models may have the same overall accuracy but fail in very different ways. One model may be strong on formal validity but weak on Gettier cases. Another may recognize knowledge failures but overreact to weak defeaters. Another may distinguish truth and belief but confuse pragmatic acceptance with epistemic justification.

Epistemically is designed to surface those profiles.

---

## Current status

Epistemically is currently an early prototype.

The current version includes:

* A small hand-written seed benchmark
* Four active epistemic modules
* Structured JSON model outputs
* Exact-label component scoring
* Bootstrap confidence intervals
* Module-level summaries
* Failure gallery
* Case explorer
* Radar chart for epistemic profiles
* Module by schema-family heatmap
* Streamlit dashboard with a dark visual identity

The current result file evaluates `gpt-4o-mini` on the initial draft benchmark. These results are useful for development and demonstration, but they should not be interpreted as final benchmark claims.

The project is intentionally evolving. The benchmark will need more cases, stronger schema coverage, more model runners, better reliability checks, and additional review before it should be treated as a mature leaderboard.

---

## Current v0 modules

Epistemically currently includes 24 seed cases across four active modules, with additional modules planned.

| Module                   | What it tests                                                                                                        |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| `gettier_luck`           | Whether a model distinguishes knowledge from lucky true belief in Gettier-style and epistemic luck cases.            |
| `belief_truth_knowledge` | Whether a model separates belief, truth, justification, acceptance, and knowledge.                                   |
| `deduction_rationality`  | Whether a model recognizes valid inference, invalid inference, contradiction, and rational consistency requirements. |
| `defeaters`              | Whether a model updates appropriately when new evidence weakens, rebuts, undercuts, or fails to affect a belief.     |
| `induction_updating`     | Planned module for inductive reasoning, probabilistic support, and evidence updating.                                |

The current module structure is intentionally modular. Epistemically can grow into a broader evaluation suite while keeping each case inspectable and each score explainable.

---

## Module 1: Epistemic luck and Gettier cases

The `gettier_luck` module is the flagship module.

It evaluates cases where an agent may have:

* a belief
* a true target proposition
* some justification
* an apparent route to the truth
* but no knowledge because the truth is too lucky

The target failure mode is the classic epistemic mistake of treating justified true belief as sufficient for knowledge.

Example pattern:

```text
An agent has evidence that appears to support p.
The agent believes p.
p is true.
However, the agent's route to p depends on a false premise, a misleading environment, or a lucky connection between evidence and truth.
Question: Does the agent know p?
```

The expected answer may be:

```json
{
  "belief_status": "believes",
  "truth_status": "true",
  "justification_status": "justified",
  "knowledge_status": "does_not_know",
  "epistemic_status": "lucky_true_belief"
}
```

This is the kind of case where a model can appear superficially correct while still making an important epistemic error.

Future versions of this module may distinguish several families of epistemic luck:

* Gettier-style justified true belief without knowledge
* False-lemma cases
* Fake-object or real-counterpart cases
* Environmental luck
* Intervening luck
* Modal safety failures

The public-facing dashboard can keep these categories simple, while the dataset metadata can preserve more fine-grained schema information for analysis.

---

## Module 2: Belief, truth, justification, and knowledge

The `belief_truth_knowledge` module tests whether a model can separate basic epistemic components.

A case may ask whether an agent:

* believes the target proposition
* accepts it only for practical purposes
* has epistemic justification
* has only pragmatic motivation
* is correct about the target proposition
* knows the target proposition

This module is important because many epistemic failures come from collapsing these distinctions.

For example, an agent might accept a proposition for practical purposes without believing it. Or they might believe something true without justification. Or they might have justification for a false belief. Or they might have a true justified belief that still fails to be knowledge because of luck.

Epistemically evaluates these components separately instead of hiding them inside one broad answer.

---

## Module 3: Rational inference

The `deduction_rationality` module evaluates whether a model can recognize basic valid and invalid inference patterns.

Current schema families include:

* contradiction
* consistency
* modus ponens
* modus tollens
* affirming the consequent
* denying the antecedent
* hypothetical syllogism
* disjunctive syllogism
* constructive dilemma
* simplification
* addition

The point is not just to test formal logic in isolation. The point is to test whether a model can separate:

* whether an inference is valid
* whether a conclusion follows from premises
* whether an agent is rationally committed to a conclusion
* whether the premise beliefs are true
* whether the agent knows the conclusion

This distinction matters because validity does not require true premises, and knowledge does not automatically follow from every valid-looking inference in every context.

---

## Module 4: Defeaters and belief revision

The `defeaters` module evaluates whether a model responds appropriately when new evidence affects an existing belief.

This module currently prioritizes **belief revision behavior** over fine-grained taxonomy.

For v0, the main defeater labels are:

* `none_placebo`
* `rebutting_defeater`
* `undercutting_defeater`
* `higher_order_defeater`

The model may output a `defeater_type`, but this field is currently diagnostic rather than part of the primary score. The primary score focuses on whether the model updates appropriately.

Possible update decisions include:

* retain belief
* reduce confidence
* suspend judgment
* believe not-p
* leave confidence unchanged when the information is irrelevant

This design avoids over-penalizing reasonable taxonomy disputes while still testing the main epistemic behavior: whether the model recognizes when belief revision is rationally required.

---

## What the prototype does

The current prototype includes:

* 24 hand-written epistemic evaluation cases
* OpenAI runner for model evaluation
* Structured JSON-only model outputs
* Exact-label component scoring
* Weighted field-level scores
* Bootstrap confidence intervals
* Module-level score summaries
* Failure gallery
* Case explorer
* Radar chart for model epistemic profile
* Module by schema-family heatmap
* Dark Streamlit dashboard with orange and coral visual identity

The current seed result file evaluates `gpt-4o-mini` on the 24-case draft benchmark. This is a prototype result, not a final benchmark claim.

---

## Methodology

Each evaluation item is an epistemic case. A case includes:

* `id`
* `module`
* `schema_family`
* `scenario`
* `target_proposition`
* `question`
* `expected` structured labels
* `scoring_weights`
* `difficulty`
* `notes`

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

Future versions may add secondary semantic scoring, explanation-quality scoring, or human-reviewed partial credit. But exact component scoring is the foundation because it is transparent, auditable, and easy to debug.

---

## Statistics

Epistemically reports:

* Mean score by model
* Mean score by module
* Mean score by schema family
* Bootstrap confidence intervals
* Field-level correctness
* Failure counts
* Failure examples
* Module profile radar charts
* Module by schema-family heatmaps

The bootstrap intervals are intended to show uncertainty over the current case set. They should not be overinterpreted as final population-level claims, especially while the benchmark is still small.

As the dataset grows, Epistemically can support stronger model comparisons, including paired bootstrap differences across models evaluated on the same cases.

---

## Dashboard

The Streamlit dashboard is designed as an AI epistemology lab interface.

Current views include:

### Overview

High-level model performance:

* Overall epistemic score
* Cases evaluated
* Failure count
* Strongest module
* Weakest module
* Points earned and possible
* Module score chart with confidence intervals

### Module Profile

A compact view of the model's epistemic strengths and weaknesses:

* Radar chart across modules
* Module by schema-family heatmap
* Interpretive summary

### Failure Gallery

A card-based review of imperfect cases, showing:

* Scenario
* Target proposition
* Expected labels
* Model labels
* Per-field correctness
* Model explanation
* Score

This is where the evaluation becomes most useful. Many failures are not just wrong answers. They are specific epistemic confusions, such as treating a lucky true belief as knowledge, confusing an invalid inference with a false conclusion, or revising a belief in response to irrelevant information.

### Case Explorer

A detailed case-level interface for inspecting any result row.

### Methodology

A concise explanation of what the tool measures, how scoring works, and what the current limitations are.

---

## Example failure patterns

The current prototype already surfaces interesting model behavior.

Examples of failure types include:

* Correctly identifying belief, truth, defective justification, and epistemic luck, while still summarizing the case as `false_belief` instead of `lucky_true_belief`.
* Recognizing that an agent's commitments are inconsistent while misclassifying a modus ponens inference as invalid.
* Correctly identifying that a subject does not believe a true proposition, while still summarizing the case as a false belief.
* Treating a true belief as knowledge even when the connection between justification and truth is lucky.
* Updating a belief in response to information that is irrelevant to the target proposition.

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

The dashboard runs from the committed CSV results in `data/results/` and makes no API calls, so no secrets are required to view it. `OPENAI_API_KEY` is only needed for future live evaluation runs through `scripts/run_eval.py`, not for viewing the current dashboard.

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

* The seed benchmark is small.
* Cases are hand-written and need further review.
* Some schema families need more examples.
* Defeater cases need more difficult variants.
* Epistemic luck cases need broader schema coverage.
* The current runner supports OpenAI only.
* Scores depend on the quality and clarity of the gold labels.
* Exact-label scoring is transparent but can be brittle.
* The benchmark is not yet large enough for strong leaderboard-style claims.

This project should currently be understood as a working prototype and research/product direction, not a finished benchmark.

---

## Roadmap

### v0: Working prototype

Current state:

* OpenAI runner
* 24 seed cases
* Exact-label scoring
* Bootstrap confidence intervals
* Streamlit dashboard
* Dark UI
* Failure gallery
* Case explorer
* Module radar chart
* Module by schema-family heatmap

### v0.1: Stronger benchmark foundation

Near-term improvements:

* Expand to 50 to 100 curated cases
* Make epistemic luck the strongest and clearest module
* Improve gold-label consistency
* Add paraphrase variants
* Add case difficulty tags
* Add stronger schema-family coverage
* Add clearer failure taxonomies
* Add more challenging defeater cases
* Add robustness checks across repeated model calls

### MVP: Public demo

Deployment-focused improvements:

* Deploy public dashboard
* Connect `epistemically.com`
* Add polished documentation
* Add screenshots and demo GIFs
* Include one or more stable model result files
* Add methodology page in the dashboard
* Improve mobile responsiveness

### v1: Multi-model evaluation

Model-comparison work:

* Add Anthropic runner
* Add Gemini runner
* Add local or open-weight model support if practical
* Add model comparison dashboard
* Add paired bootstrap difference estimates
* Add model by module heatmaps
* Add repeated-run stability metrics
* Add exportable reports

### v2: Dataset expansion and reliability

Benchmark-quality work:

* Expand to 250 to 500 reviewed cases
* Add generated variants with manual review
* Add schema-family bootstrapping
* Estimate case difficulty
* Track inter-reviewer agreement for gold labels
* Add reliability and stability analysis
* Separate primary scores from diagnostic fields
* Improve partial-credit options without relying on LLM judges

### v3: Epistemic Theory Profile

A future module may evaluate how a model's structured responses pattern across classic epistemological questions.

This would not claim that a model literally "is a reliabilist" or "believes contextualism." Instead, it would behaviorally profile outputs as resembling epistemological positions under controlled prompts.

Potential theory families:

* Reliabilism
* Evidentialism
* Internalism
* Externalism
* Foundationalism
* Coherentism
* Virtue epistemology
* Contextualism
* Knowledge-first epistemology
* Pragmatic encroachment
* Safety and sensitivity theories
* Testimony and social epistemology
* Assertion norms

This module should separate two tasks:

1. **View classification**
   Can the model correctly identify a philosophical view from a structured description?

2. **Behavioral profile inference**
   Across structured answers, what epistemological patterns do the model's outputs resemble?

Possible visualizations:

* Epistemic compass
* Theory radar chart
* Model profile card
* Disagreement and instability map
* Theory-family heatmap

The framing should remain careful:

> The model's outputs exhibit a pattern resembling a view. The model does not literally hold that view.

---

## Longer-term ideas

Potential future directions:

* Explanation-quality scoring
* Calibration curves
* Bayesian or hierarchical score estimates
* Active generation of hard cases
* Human review interface for gold labels
* Model self-consistency checks
* Cross-prompt robustness testing
* Public comparison reports
* Epistemic error taxonomy
* Leaderboard only after benchmark quality improves

---

## Related work

Epistemically is related to work on:

* LLM factuality
* Hallucination evaluation
* Truthfulness benchmarks
* Theory-of-mind benchmarks
* Belief revision
* Defeasible reasoning
* Epistemic calibration
* Gettier-style epistemic luck
* Structured model evaluation frameworks

The goal is not to replace those projects. The goal is to build a practical, inspectable evaluation suite organized around epistemological case types, behavioral model outputs, component-level scoring, and statistical model profiles.

See:

* `docs/methodology.md`
* `docs/related_work.md`

---

## License

MIT License.
