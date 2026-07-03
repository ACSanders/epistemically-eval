"""Simple bootstrap confidence intervals for mean scores."""

from typing import Optional, Sequence, Tuple

import numpy as np


def bootstrap_mean_ci(
    scores: Sequence[float],
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: Optional[int] = None,
) -> Tuple[float, float, float]:
    """Percentile bootstrap CI for the mean of ``scores``.

    Returns (mean, ci_low, ci_high). With a single observation the interval
    collapses to the point estimate.
    """
    values = np.asarray(scores, dtype=float)
    if values.size == 0:
        raise ValueError("scores is empty")
    mean = float(values.mean())
    if values.size == 1:
        return mean, mean, mean

    rng = np.random.default_rng(seed)
    idx = rng.integers(0, values.size, size=(n_resamples, values.size))
    resample_means = values[idx].mean(axis=1)
    alpha = (1.0 - confidence) / 2.0
    ci_low, ci_high = np.quantile(resample_means, [alpha, 1.0 - alpha])
    return mean, float(ci_low), float(ci_high)


def paired_bootstrap_diff(
    scores_a: Sequence[float],
    scores_b: Sequence[float],
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: Optional[int] = None,
) -> Tuple[float, float, float]:
    """Percentile bootstrap CI for mean(a - b) over paired scores.

    Both sequences must be aligned case-by-case (same cases, same order).
    Returns (mean_diff, ci_low, ci_high); an interval excluding 0 suggests a
    real difference between the two models on this case set.
    """
    a = np.asarray(scores_a, dtype=float)
    b = np.asarray(scores_b, dtype=float)
    if a.size != b.size:
        raise ValueError(f"paired scores must be same length ({a.size} vs {b.size})")
    diffs = a - b
    return bootstrap_mean_ci(diffs, n_resamples=n_resamples, confidence=confidence, seed=seed)
