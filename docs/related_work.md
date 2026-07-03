# Related work

Short pointers situating Epistemically. This is a working list, not a survey.

## Behavioral evaluation of epistemic-adjacent capabilities

- **TruthfulQA** (Lin et al., 2022) — measures whether models avoid asserting
  common falsehoods. Overlaps with our fact dimension, but does not separate
  belief attribution from truth or probe justification.
- **Theory-of-mind benchmarks** — ToMi (Le et al., 2019), BigToM (Gandhi et
  al., 2023), FANToM (Kim et al., 2023) test false-belief attribution to
  agents in stories. Our `belief_truth_knowledge` module is close in spirit but
  asks for belief, knowledge, and fact judgments jointly, which is where the
  interesting dissociations show up.
- **Epistemic reasoning in LLMs** — work on knowledge/belief distinctions in
  models (e.g. "Language models' knowledge of epistemic modality," and studies
  of LLM performance on epistemic logic puzzles) shows models often conflate
  "the agent believes p" with "p is true."
- **Calibration and honesty evals** — e.g. Kadavath et al. (2022), "Language
  Models (Mostly) Know What They Know." Complementary: they study a model's
  confidence in its own answers; we study its competence at third-person
  epistemic judgments.

## Philosophical sources for case design

- **Gettier (1963), "Is Justified True Belief Knowledge?"** — the template for
  our epistemic-luck module.
- **Russell's stopped clock** (1948) and **Goldman's fake barns** (1976) — the
  two classic luck structures used in `sample_cases.jsonl`.
- **Pollock (1986)** on undercutting vs. rebutting defeaters — the basis of
  the `defeaters` module, including defeater-defeaters.
- **Experimental philosophy** (e.g. Machery et al. on cross-cultural Gettier
  intuitions) — a caution: expected labels follow mainstream textbook
  verdicts, which are majority but not universal human judgments.

## Positioning

Existing benchmarks mostly test one epistemic dimension at a time (truth,
false belief, logic). Epistemically's contribution is small but specific:
structured cases that require *joint* labels across belief, justification,
truth, and knowledge, with component scoring, so that characteristic failure
patterns (e.g. granting knowledge whenever a belief is true) are directly
visible.
