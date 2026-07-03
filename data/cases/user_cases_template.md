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

## Template: defeater case

```json
{"id": "def-100", "module": "defeaters", "schema_family": "undercutting_defeater", "variant_id": 1, "scenario": "Describe an agent forming a belief from some evidence, then receiving new information that undermines either the evidence (undercutting) or the proposition itself (rebutting).", "target_proposition": "The proposition the agent initially came to believe.", "question": "Was the agent's belief justified before the new information, is it justified after, and should the agent retain the belief?", "expected": {"justified_before": true, "justified_after": false, "should_retain_belief": false}, "scoring_weights": {"justified_before": 1.0, "justified_after": 1.5, "should_retain_belief": 1.5}, "difficulty": "medium", "notes": "Say whether the defeater is undercutting or rebutting, and whether anything later defeats the defeater."}
```
