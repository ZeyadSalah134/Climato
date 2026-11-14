"""Ordinary least squares linear trend estimation.

Model::

    y(t) = beta0 + beta1 * t + epsilon

where ``t`` is elapsed time in **years** from the first observation (so the
slope is directly interpretable as a rate of change per year, independent of
sampling frequency).
"""

from __future__ import annotations

import numpy as np
from scipy import stats

from app.core.errors import InsufficientDataError
from app.schemas.analysis import LinearTrendResult
from app.statistics.types import Series, units_per_decade_label, units_per_year_label

MIN_OBSERVATIONS = 3


def compute_linear_trend(series: Series, alpha: float = 0.05) -> LinearTrendResult:
    """Fit an OLS linear trend and return a fully populated result."""
    n = series.n
    if n < MIN_OBSERVATIONS:
        raise InsufficientDataError(
            f"Ordinary least squares requires at least {MIN_OBSERVATIONS} observations; received {n}.",
            details={"n_observations": n, "required": MIN_OBSERVATIONS},
        )

    x = series.elapsed_years()
    y = series.values

    if np.allclose(y, y[0]):
        # Constant series: slope is exactly zero and the regression is degenerate.
        return LinearTrendResult(
            slope_per_year=0.0,
            slope_per_decade=0.0,
            intercept=float(y[0]),
            standard_error=0.0,
            p_value=1.0,
            r_squared=0.0,
            adjusted_r_squared=0.0,
            confidence_interval_95=(0.0, 0.0),
            confidence_interval_95_per_decade=(0.0, 0.0),
            t_statistic=0.0,
            degrees_of_freedom=max(n - 2, 0),
            direction="no_detectable_trend",
            significant=False,
            significance="not_significant",
            n_observations=n,
            units_per_year=units_per_year_label(series.units),
            units_per_decade=units_per_decade_label(series.units),
        )

    regression = stats.linregress(x, y)
    slope = float(regression.slope)
    intercept = float(regression.intercept)
    stderr = float(regression.stderr)
    p_value = float(regression.pvalue)
    r_squared = float(regression.rvalue) ** 2
    dof = n - 2

    t_crit = float(stats.t.ppf(1 - alpha / 2, dof)) if dof > 0 else 0.0
    half_width = t_crit * stderr
    ci = (slope - half_width, slope + half_width)

    if dof > 0:
        adjusted_r_squared = 1 - (1 - r_squared) * (n - 1) / dof
    else:
        adjusted_r_squared = 0.0

    significant = bool(p_value < alpha and not np.isnan(p_value))
    if significant:
        direction = "increasing" if slope > 0 else "decreasing"
    else:
        direction = "no_detectable_trend"

    return LinearTrendResult(
        slope_per_year=slope,
        slope_per_decade=slope * 10.0,
        intercept=intercept,
        standard_error=stderr,
        p_value=p_value,
        r_squared=r_squared,
        adjusted_r_squared=adjusted_r_squared,
        confidence_interval_95=(float(ci[0]), float(ci[1])),
        confidence_interval_95_per_decade=(float(ci[0] * 10), float(ci[1] * 10)),
        t_statistic=float(regression.slope / stderr) if stderr > 0 else 0.0,
        degrees_of_freedom=dof,
        direction=direction,
        significant=significant,
        significance="significant" if significant else "not_significant",
        n_observations=n,
        units_per_year=units_per_year_label(series.units),
        units_per_decade=units_per_decade_label(series.units),
    )


def fitted_line(series: Series, slope: float, intercept: float) -> np.ndarray:
    return intercept + slope * series.elapsed_years()


def confidence_band(series: Series, alpha: float = 0.05) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (fitted, lower, upper) for the regression mean response.

    The band is the ``100*(1-alpha)%`` confidence interval for the expected
    value of ``y`` at each observed time, not a prediction interval.
    """
    x = series.elapsed_years()
    y = series.values
    n = series.n
    if n < MIN_OBSERVATIONS or np.allclose(y, y[0]):
        flat = np.full(n, float(y[0]) if n else 0.0)
        return flat, flat, flat

    regression = stats.linregress(x, y)
    slope = float(regression.slope)
    intercept = float(regression.intercept)
    stderr = float(regression.stderr)
    dof = n - 2

    fitted = intercept + slope * x
    residuals = y - fitted
    sse = float(np.sum(residuals**2))
    s_resid = float(np.sqrt(sse / dof)) if dof > 0 else 0.0
    x_bar = float(np.mean(x))
    sxx = float(np.sum((x - x_bar) ** 2))
    if sxx <= 0:
        return fitted, fitted, fitted
    se_fit = s_resid * np.sqrt(1.0 / n + (x - x_bar) ** 2 / sxx)
    t_crit = float(stats.t.ppf(1 - alpha / 2, dof)) if dof > 0 else 0.0
    return fitted, fitted - t_crit * se_fit, fitted + t_crit * se_fit
