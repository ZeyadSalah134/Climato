"""Mann-Kendall non-parametric trend test.

The Mann-Kendall test evaluates whether a monotonic trend is present without
assuming linearity or normality.  This module implements the standard
tie-corrected formulation and, when ``pymannkendall`` is installed, validates
its own output against that library in the test suite.

Formulation
-----------
``S = sum_{i<j} sign(x_j - x_i)``

``Var(S) = [ n(n-1)(2n+5) - sum_t t(t-1)(2t+5) ] / 18``

The Z statistic applies a continuity correction of +/-1 depending on the sign
of ``S``.  The p-value is two-sided.

Assumptions and caveats
-----------------------
* Observations are assumed to be independent.  Positive serial
  autocorrelation inflates the false-positive rate; the caller is warned when
  the lag-1 autocorrelation of the de-trended series is high.
* Seasonality is not removed by this test.  For monthly data the caller should
  enable seasonal adjustment, which applies the test to anomalies.
"""

from __future__ import annotations

import math

import numpy as np
from scipy import stats

from app.core.errors import InsufficientDataError
from app.schemas.analysis import MannKendallResult
from app.statistics.types import Series

MIN_OBSERVATIONS = 4
AUTOCORRELATION_WARNING_THRESHOLD = 0.3


def _sign(value: float) -> int:
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def mann_kendall_s(sample: np.ndarray) -> float:
    """Return the Mann-Kendall statistic ``S`` with O(n^2) tie-agnostic summation."""
    n = len(sample)
    s = 0.0
    for i in range(n - 1):
        s += float(np.sum(np.sign(sample[i + 1 :] - sample[i])))
    return s


def _tie_correction(sample: np.ndarray) -> float:
    _, counts = np.unique(sample, return_counts=True)
    ties = counts[counts > 1]
    if ties.size == 0:
        return 0.0
    return float(np.sum(ties * (ties - 1) * (2 * ties + 5)))


def _lag1_autocorrelation(sample: np.ndarray) -> float:
    if len(sample) < 3:
        return 0.0
    centered = sample - np.mean(sample)
    denom = float(np.sum(centered**2))
    if denom == 0:
        return 0.0
    return float(np.sum(centered[:-1] * centered[1:]) / denom)


def compute_mann_kendall(series: Series, alpha: float = 0.05) -> MannKendallResult:
    sample = series.values
    n = series.n
    if n < MIN_OBSERVATIONS:
        raise InsufficientDataError(
            f"The Mann-Kendall test requires at least {MIN_OBSERVATIONS} observations; received {n}.",
            details={"n_observations": n, "required": MIN_OBSERVATIONS},
        )

    s = mann_kendall_s(sample)
    variance = (n * (n - 1) * (2 * n + 5) - _tie_correction(sample)) / 18.0
    variance = max(variance, 0.0)

    if variance > 0:
        if s > 0:
            z = (s - 1) / math.sqrt(variance)
        elif s < 0:
            z = (s + 1) / math.sqrt(variance)
        else:
            z = 0.0
    else:
        z = 0.0

    p_value = float(2 * (1 - stats.norm.cdf(abs(z))))
    p_value = min(max(p_value, 0.0), 1.0)

    denominator = n * (n - 1) / 2.0
    tau = float(s / denominator) if denominator > 0 else 0.0

    significant = bool(p_value < alpha)
    if significant:
        trend = "increasing" if s > 0 else "decreasing"
    else:
        trend = "no_detectable_trend"

    autocorr = _lag1_autocorrelation(np.asarray(sample, dtype=float))
    autocorr_risk = bool(abs(autocorr) > AUTOCORRELATION_WARNING_THRESHOLD and n < 50)

    note = (
        "Mann-Kendall is a non-parametric monotonic trend test that does not "
        "assume normality. It assumes serial independence."
    )
    if autocorr_risk:
        note += (
            " Lag-1 autocorrelation of the series exceeds "
            f"{AUTOCORRELATION_WARNING_THRESHOLD}, so the p-value may be optimistic; "
            "interpret the result with caution or enable seasonal adjustment."
        )

    return MannKendallResult(
        trend=trend,
        tau=tau,
        s=s,
        z=float(z),
        p_value=p_value,
        variance_s=variance,
        significant=significant,
        significance="significant" if significant else "not_significant",
        n_observations=n,
        autocorrelation_risk=autocorr_risk,
        note=note,
    )
