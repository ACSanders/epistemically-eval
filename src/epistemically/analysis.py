"""Aggregation helpers over results CSVs produced by the runner."""

from pathlib import Path
from typing import Union

import pandas as pd

from epistemically.bootstrap import bootstrap_mean_ci


def load_results(path: Union[str, Path]) -> pd.DataFrame:
    """Load a results CSV written by the runner."""
    return pd.read_csv(path)


def summarize_by_model_module(df: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Mean score with bootstrap CI, grouped by (model, module)."""
    rows = []
    for (model, module), group in df.groupby(["model", "module"]):
        scores = group["score"].dropna().tolist()
        if not scores:
            continue
        mean, ci_low, ci_high = bootstrap_mean_ci(scores, seed=seed)
        rows.append(
            {
                "model": model,
                "module": module,
                "n_cases": len(scores),
                "mean_score": round(mean, 4),
                "ci_low": round(ci_low, 4),
                "ci_high": round(ci_high, 4),
            }
        )
    return pd.DataFrame(rows)


def failures(df: pd.DataFrame, threshold: float = 1.0) -> pd.DataFrame:
    """Rows scoring below ``threshold``, worst first."""
    out = df[df["score"] < threshold].copy()
    return out.sort_values("score").reset_index(drop=True)
