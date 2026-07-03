"""Pydantic models for evaluation cases and scoring results."""

from typing import Dict, Literal, Union

from pydantic import BaseModel, Field, model_validator

Module = Literal[
    "belief_truth_knowledge",
    "gettier_luck",
    "deduction_rationality",
    "defeaters",
    "induction_updating",
]

# Label values are booleans for v0, but strings are allowed so future modules
# can use categorical labels without a schema change.
LabelValue = Union[bool, str]


class EpistemicCase(BaseModel):
    """One evaluation case.

    ``expected`` maps label names (e.g. "belief", "knowledge", "entailed") to
    expected values. Modules use different label sets, so the mapping is
    intentionally open-ended rather than fixed per module.
    """

    id: str
    module: Module
    schema_family: str
    variant_id: int
    scenario: str
    target_proposition: str
    question: str
    expected: Dict[str, LabelValue]
    scoring_weights: Dict[str, float] = Field(default_factory=dict)
    difficulty: Literal["easy", "medium", "hard"]
    notes: str = ""

    @model_validator(mode="after")
    def _weights_refer_to_expected_labels(self) -> "EpistemicCase":
        unknown = set(self.scoring_weights) - set(self.expected)
        if unknown:
            raise ValueError(
                f"case {self.id}: scoring_weights refer to unknown labels {sorted(unknown)}"
            )
        return self

    def weight_for(self, label: str) -> float:
        """Weight for a label; labels without an explicit weight count 1.0."""
        return self.scoring_weights.get(label, 1.0)


class ScoreResult(BaseModel):
    """Component scoring outcome for one case."""

    per_field: Dict[str, bool]
    points: float
    max_points: float
    score: float  # points / max_points, in [0, 1]
