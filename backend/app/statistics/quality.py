"""Data quality assessment performed before statistical testing.

The goal is to detect conditions under which a trend test would be misleading
or underpowered, and to report them explicitly rather than silently producing
numbers.
"""

from __future__ import annotations

from datetime import date

import numpy as np

from app.schemas.analysis import DataQuality, QualityCheck
from app.statistics.types import Series

# Minimum number of valid observations required to run a trend analysis.
# These are deliberately conservative defaults and are documented in
# docs/SCIENTIFIC_METHODS.md.
MIN_OBSERVATIONS_MONTHLY = 24  # two years of monthly means
MIN_OBSERVATIONS_DAILY = 180  # roughly half a year of daily values
MIN_PERIOD_YEARS = 2.0
MAX_MISSING_PCT = 40.0
AUTOCORRELATION_WARNING_THRESHOLD = 0.3


def minimum_observations(frequency: str) -> int:
    return MIN_OBSERVATIONS_DAILY if frequency == "daily" else MIN_OBSERVATIONS_MONTHLY


def _expected_count(series: Series) -> int:
    if series.n == 0:
        return 0
    first, last = series.dates[0], series.dates[-1]
    days = (last - first).days
    if series.frequency == "daily":
        return days + 1
    return (last.year - first.year) * 12 + (last.month - first.month) + 1


def _lag1_autocorrelation(residuals: np.ndarray) -> float | None:
    if len(residuals) < 3:
        return None
    centered = residuals - np.mean(residuals)
    denom = float(np.sum(centered**2))
    if denom == 0:
        return None
    return float(np.sum(centered[:-1] * centered[1:]) / denom)


def _detrend(values: np.ndarray, t: np.ndarray) -> np.ndarray:
    if len(values) < 2 or np.allclose(values, values[0]):
        return values - np.mean(values)
    slope, intercept = np.polyfit(t, values, 1)
    return values - (intercept + slope * t)


def assess_quality(
    series: Series,
    *,
    n_missing: int = 0,
    requested_start: date | None = None,
    requested_end: date | None = None,
) -> DataQuality:
    n = series.n
    expected = _expected_count(series)
    checks: list[QualityCheck] = []
    warnings: list[str] = []

    period_start = series.dates[0] if n else None
    period_end = series.dates[-1] if n else None
    period_years = 0.0
    if period_start and period_end:
        period_years = (period_end - period_start).days / 365.25

    total_expected = (n + n_missing) if (n + n_missing) > 0 else expected
    missing_pct = (n_missing / total_expected * 100.0) if total_expected > 0 else 0.0

    is_constant = bool(n > 0 and np.allclose(series.values, series.values[0]))

    required = minimum_observations(series.frequency)
    sufficient = n >= required and period_years >= MIN_PERIOD_YEARS

    # --- individual checks -------------------------------------------------
    if n >= required:
        checks.append(QualityCheck(name="observation_count", status="pass", message=f"{n} valid observations."))
    else:
        checks.append(
            QualityCheck(
                name="observation_count",
                status="fail",
                message=f"Only {n} valid observations; at least {required} are required.",
            )
        )
        warnings.append(f"Insufficient observations ({n} < {required}).")

    if period_years >= MIN_PERIOD_YEARS:
        checks.append(
            QualityCheck(
                name="period_length",
                status="pass",
                message=f"Analysed period spans {period_years:.1f} years.",
            )
        )
    else:
        checks.append(
            QualityCheck(
                name="period_length",
                status="fail",
                message=f"Analysed period spans only {period_years:.1f} years; at least {MIN_PERIOD_YEARS:.0f} are required.",
            )
        )
        warnings.append(f"Observation period too short ({period_years:.1f} years).")

    if is_constant:
        checks.append(
            QualityCheck(
                name="variance",
                status="warning",
                message="The series is constant; no trend can be estimated.",
            )
        )
        warnings.append("Constant series: all values are identical.")
    else:
        checks.append(QualityCheck(name="variance", status="pass", message="Series exhibits variance."))

    if missing_pct > MAX_MISSING_PCT:
        checks.append(
            QualityCheck(
                name="missing_data",
                status="warning",
                message=f"{missing_pct:.1f}% of expected observations are missing.",
            )
        )
        warnings.append(f"High missing-data fraction ({missing_pct:.1f}%).")
    else:
        checks.append(
            QualityCheck(
                name="missing_data",
                status="pass",
                message=f"{missing_pct:.1f}% missing.",
            )
        )

    # --- autocorrelation of de-trended series ------------------------------
    autocorr: float | None = None
    autocorr_warning = False
    if n >= 8 and not is_constant:
        t = series.elapsed_years()
        residuals = _detrend(series.values, t)
        autocorr = _lag1_autocorrelation(residuals)
        if autocorr is not None and abs(autocorr) > AUTOCORRELATION_WARNING_THRESHOLD:
            autocorr_warning = True
            checks.append(
                QualityCheck(
                    name="autocorrelation",
                    status="warning",
                    message=f"Lag-1 autocorrelation is {autocorr:.2f}, which may inflate significance.",
                )
            )
            warnings.append(
                f"Residual lag-1 autocorrelation ({autocorr:.2f}) exceeds "
                f"{AUTOCORRELATION_WARNING_THRESHOLD}; significance may be optimistic."
            )
        else:
            checks.append(
                QualityCheck(
                    name="autocorrelation",
                    status="pass",
                    message="No strong residual autocorrelation detected.",
                )
            )

    # --- irregular sampling ------------------------------------------------
    irregular = False
    if series.frequency == "monthly" and n >= 3:
        gaps = [
            (series.dates[i + 1].year - series.dates[i].year) * 12
            + (series.dates[i + 1].month - series.dates[i].month)
            for i in range(n - 1)
        ]
        if gaps and max(gaps) > 1:
            irregular = True
            checks.append(
                QualityCheck(
                    name="sampling",
                    status="warning",
                    message="Monthly series contains gaps (irregular sampling).",
                )
            )
            warnings.append("Irregular sampling: some months are absent from the record.")
        else:
            checks.append(QualityCheck(name="sampling", status="pass", message="Regular monthly sampling."))

    # --- incomplete first/last period -------------------------------------
    if requested_start and period_start and period_start > requested_start:
        checks.append(
            QualityCheck(
                name="coverage_start",
                status="warning",
                message=f"Data begins {period_start.isoformat()}, after the requested {requested_start.isoformat()}.",
            )
        )
    if requested_end and period_end and period_end < requested_end:
        checks.append(
            QualityCheck(
                name="coverage_end",
                status="warning",
                message=f"Data ends {period_end.isoformat()}, before the requested {requested_end.isoformat()}.",
            )
        )

    return DataQuality(
        n_valid=n,
        n_expected=max(expected, n + n_missing),
        n_missing=n_missing,
        missing_pct=round(missing_pct, 2),
        period_start=period_start,
        period_end=period_end,
        period_years=round(period_years, 2),
        is_constant=is_constant,
        lag1_autocorrelation=round(autocorr, 3) if autocorr is not None else None,
        autocorrelation_warning=autocorr_warning,
        irregular_sampling=irregular,
        min_observations_required=required,
        sufficient=sufficient,
        checks=checks,
        warnings=warnings,
    )
