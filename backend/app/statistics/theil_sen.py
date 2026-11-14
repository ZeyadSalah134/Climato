"""Theil-Sen robust slope estimator.

The Theil-Sen estimator is the median of the pairwise slopes between all
observation pairs.  It is resistant to outliers and is reported alongside the
ordinary least squares slope so the two can be compared.
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from app.core.errors import InsufficientDataError
from app.schemas.analysis import TheilSenResult
from app.statistics.types import Series, units_per_decade_label, units_per_year_label

MIN_OBSERVATIONS = 3


def compute_theil_sen(series: Series, alpha: float = 0.05) -> TheilSenResult:
    n = series.n
    if n < MIN_OBSERVATIONS:
        raise InsufficientDataError(
            f"The Theil-Sen estimator requires at least {MIN_OBSERVATIONS} observations; received {n}.",
            details={"n_observations": n, "required": MIN_OBSERVATIONS},
        )

    x = series.elapsed_years()
    y = series.values

    if np.allclose(y, y[0]):
        return TheilSenResult(
            slope_per_year=0.0,
            slope_per_decade=0.0,
            intercept=float(y[0]),
            confidence_interval_95=(0.0, 0.0),
            confidence_interval_95_per_decade=(0.0, 0.0),
            direction="no_detectable_trend",
            n_observations=n,
            units_per_year=units_per_year_label(series.units),
            units_per_decade=units_per_decade_label(series.units),
        )

    slope, intercept, low, high = stats.theilslopes(y, x, alpha=1 - alpha)

    if slope > 0:
        direction = "increasing"
    elif slope < 0:
        direction = "decreasing"
    else:
        direction = "no_detectable_trend"

    return TheilSenResult(
        slope_per_year=float(slope),
        slope_per_decade=float(slope) * 10.0,
        intercept=float(intercept),
        confidence_interval_95=(float(low), float(high)),
        confidence_interval_95_per_decade=(float(low) * 10, float(high) * 10),
        direction=direction,  # type: ignore[arg-type]
        n_observations=n,
        units_per_year=units_per_year_label(series.units),
        units_per_decade=units_per_decade_label(series.units),
    )
