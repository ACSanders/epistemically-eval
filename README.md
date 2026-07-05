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
