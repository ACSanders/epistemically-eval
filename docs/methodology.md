# Methodology

## Framing

Epistemically evaluates model *behavior*, not model minds. Cases describe an
agent in a scenario and ask the model to judge the epistemic status of a
target proposition — does the agent believe it, know it, is it a fact, is a
conclusion entailed, does new evidence defeat justification. A model scores
well when its output labels track the distinctions competent human judges
draw on the same cases. No claim is made that the model itself believes or
knows anything.

## Case format

Cases live in JSONL, one object per line, validated by
`epistemically.schemas.EpistemicCase`:

- `id`, `module`, `schema_family`, `variant_id` — identity and grouping.
  A schema family is a reusable scenario template (e.g. `stopped_clock`);
  variants are surface rewrites of the same template, which supports checking
  consistency across paraphrases later.
- `scenario`, `target_proposition`, `question` — the text shown to the model.
- `expected` — a mapping from label names to expected values. Label sets vary
  by module (e.g. `belief`/`knowledge`/`fact` vs. `entailed`).
- `scoring_weights` — optional per-label weights; unlisted labels weigh 1.0.
- `difficulty`, `notes` — human-facing metadata.

## v0 modules

| Module | What it probes |
| --- | --- |
| `belief_truth_knowledge` | Separating an agent's belief from truth and from knowledge |
| `gettier_luck` | Justified true belief without knowledge (epistemic luck) |
| `deduction_rationality` | Entailment recognition and rational consistency of assertion |
| `defeaters` | Justification updates under undercutting/rebutting evidence |
| `induction_updating` | Inductive inference and evidence updating (no seed cases yet) |

## Scoring

v0 uses exact-label component scoring (`epistemically.scoring`). Each
expected label is compared to the model's parsed JSON output after light
normalization (booleans, "yes"/"no", case). Each correct field earns its
weight; the case score is earned points over maximum points, in [0, 1].
Missing fields and unparseable responses score zero on the affected fields.
The `brief_explanation` field is collected but not scored in v0.

## Uncertainty

Mean scores per model/module come with percentile-bootstrap 95% confidence
intervals (`epistemically.bootstrap`). For comparing two models on the same
case set, a paired bootstrap on per-case score differences is provided; an
interval excluding zero suggests a real difference. With only 8 sample cases
the intervals are wide by design — v0 demonstrates the machinery, not
statistical power.

## Known limitations

- Exact-label scoring cannot credit partially correct reasoning.
- Single-run evaluation ignores sampling variance within a model
  (temperature 0 mitigates but does not eliminate this).
- Expected labels encode mainstream verdicts on standard cases; some
  (notably fake barns) are philosophically contested. The `notes` field
  records the intended reading.
- Prompt wording itself influences results; schema families and variants
  exist so that paraphrase robustness can be measured rather than assumed.
