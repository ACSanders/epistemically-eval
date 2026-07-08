# Writing your own cases

Hand-written cases go in `user_cases_draft.jsonl`, one JSON object per line
(JSONL has no comments, hence this separate guide). Copy a template below onto
a new line, fill it in, and check it with:

```bash
python scripts/validate_cases.py data/cases/user_cases_draft.jsonl
```

Field notes:

- `id` — unique across the file; the sample file uses a `module-prefix + number`
  convention (e.g. `bkf-003`, `def-003`), but any unique string works.
- `module` — one of `belief_truth_knowledge`, `gettier_luck`,
  `deduction_rationality`, `defeaters`, `induction_updating`.
- `schema_family` — the reusable scenario template this case instantiates
  (e.g. `false_belief`, `stopped_clock`); `variant_id` is an integer
  distinguishing paraphrases of the same family.
- `expected` — label names mapped to expected values (booleans for v0). The
  model is asked for exactly these fields plus `brief_explanation`.
- `scoring_weights` — optional; any label you list must exist in `expected`,
  and unlisted labels weigh 1.0. Use a higher weight for the discriminating
  judgment (the sample Gettier cases weight `knowledge` at 2.0).
- `difficulty` — `easy`, `medium`, or `hard`.
- `notes` — for humans; records the intended reading of the case.

## Template: belief/knowledge/fact case

```json
{"id": "bkf-100", "module": "belief_truth_knowledge", "schema_family": "false_belief", "variant_id": 1, "scenario": "Describe an agent, their evidence, and what is actually true. Keep it concrete and self-contained.", "target_proposition": "The single proposition being judged.", "question": "Judge the epistemic status of the target proposition for the agent: does the agent believe it, does the agent know it, and is it a fact?", "expected": {"belief": true, "knowledge": false, "fact": false}, "scoring_weights": {"belief": 1.0, "knowledge": 1.0, "fact": 1.0}, "difficulty": "easy", "notes": "What this case is meant to test, and why the expected labels are correct."}
```

## Template: defeater case (v2)

```json
{"id": "def_100_short_slug", "module": "defeaters", "schema_family": "defeater_revision", "variant_id": 1, "scenario": "Describe an agent with initial support for a target proposition p, then new information that rebuts p, undercuts the original evidence, challenges the agent's own reliability, or (for placebo cases) has no epistemic effect.", "target_proposition": "The proposition p the agent initially came to believe.", "question": "How should the new information affect the agent's epistemic position regarding the target proposition?", "expected": {"defeater_present": "yes", "defeater_type": "undercutting_defeater", "defeater_strength": "moderate", "support_relation": "equal_support", "belief_revision": "suspend_judgment"}, "difficulty": "medium", "notes": "Say why the defeater has this type and strength, and note anything contested about the intended reading."}
```

Defeaters cases must define exactly these five expected labels, and the
validator additionally enforces the coherence mappings on the answer key:

- `defeater_strength` → `support_relation`: `none`→`no_impact`,
  `weak`→`target_better_supported`, `moderate`→`equal_support`,
  `strong`→`negation_better_supported`.
- `support_relation` → `belief_revision`: `no_impact` and
  `target_better_supported`→`maintain_target_belief`,
  `equal_support`→`suspend_judgment`,
  `negation_better_supported`→`believe_negation`.
- `defeater_present: "no"` requires `defeater_type: "none_placebo"` and
  `defeater_strength: "none"`; `"yes"` forbids both.

Models are scored on the five exact labels plus two computed coherence
components (see `docs/methodology.md`); the model never self-reports
coherence, so cases only need the five labels above.
