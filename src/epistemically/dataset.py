"""Loading and validating JSONL case files."""

import json
from pathlib import Path
from typing import List, Tuple, Union

from pydantic import ValidationError

from epistemically.defeaters import expected_label_problems
from epistemically.schemas import EpistemicCase

PathLike = Union[str, Path]


def load_cases(path: PathLike) -> List[EpistemicCase]:
    """Load and validate cases from a JSONL file.

    Raises ValueError on the first malformed line, invalid case, duplicate
    case id, or failed module-specific ground-truth check.
    """
    cases: List[EpistemicCase] = []
    seen_ids = set()
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{lineno}: invalid JSON: {exc}") from exc
            try:
                case = EpistemicCase.model_validate(raw)
            except ValidationError as exc:
                raise ValueError(f"{path}:{lineno}: invalid case: {exc}") from exc
            if case.id in seen_ids:
                raise ValueError(f"{path}:{lineno}: duplicate case id {case.id!r}")
            problems = expected_label_problems(case)
            if problems:
                raise ValueError(
                    f"{path}:{lineno}: case {case.id}: " + "; ".join(problems)
                )
            seen_ids.add(case.id)
            cases.append(case)
    if not cases:
        raise ValueError(f"{path}: no cases found")
    return cases


def check_cases(path: PathLike) -> Tuple[List[EpistemicCase], List[str]]:
    """Like load_cases but collects all problems instead of failing fast.

    Returns (valid_cases, error_messages). Useful for validation tooling.
    """
    cases: List[EpistemicCase] = []
    errors: List[str] = []
    seen_ids = set()
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {lineno}: invalid JSON: {exc}")
                continue
            try:
                case = EpistemicCase.model_validate(raw)
            except ValidationError as exc:
                errors.append(f"line {lineno}: invalid case: {exc}")
                continue
            if case.id in seen_ids:
                errors.append(f"line {lineno}: duplicate case id {case.id!r}")
                continue
            # Module-specific ground-truth checks (currently defeaters v2):
            # a case with an incomplete or internally incoherent answer key
            # is rejected, not silently scored.
            problems = expected_label_problems(case)
            if problems:
                errors.append(f"line {lineno}: case {case.id}: " + "; ".join(problems))
                continue
            seen_ids.add(case.id)
            cases.append(case)
    return cases, errors
