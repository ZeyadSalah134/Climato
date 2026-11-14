"""Seasonal decomposition and anomaly calculation.

For monthly data the climatological mean of each calendar month is computed
over the analysis baseline (the full analysed period) and subtracted to form
monthly anomalies.  Trends computed on anomalies describe change *beyond* the
normal seasonal cycle.
"""

from __future__ import annotations

import numpy as np

from app.schemas.analysis import MonthlyClimatology, SeasonalResult
from app.statistics.types import Series

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


def compute_climatology(series: Series) -> list[MonthlyClimatology]:
    if series.frequency != "monthly":
        return []
    buckets: dict[int, list[float]] = {m: [] for m in range(1, 13)}
    for moment, value in zip(series.dates, series.values, strict=False):
        buckets[moment.month].append(float(value))
    climatology: list[MonthlyClimatology] = []
    for month in range(1, 13):
        values = buckets[month]
        climatology.append(
            MonthlyClimatology(
                month=month,
                month_name=MONTH_NAMES[month - 1],
                mean=float(np.mean(values)) if values else 0.0,
                count=len(values),
            )
        )
    return climatology


def apply_seasonal_adjustment(series: Series) -> tuple[Series, SeasonalResult]:
    """Return the anomaly series and the seasonal metadata.

    For non-monthly series the original series is returned unchanged and the
    result records that no adjustment was applied.
    """
    if series.frequency != "monthly":
        return series, SeasonalResult(
            applied=False,
            note="Seasonal adjustment is only applied to monthly data.",
        )

    climatology = compute_climatology(series)
    means = {entry.month: entry.mean for entry in climatology}
    anomalies = np.array(
        [value - means[moment.month] for moment, value in zip(series.dates, series.values, strict=False)],
        dtype=float,
    )
    adjusted = series.with_values(anomalies)

    return adjusted, SeasonalResult(
        applied=True,
        baseline_start=series.dates[0] if series.dates else None,
        baseline_end=series.dates[-1] if series.dates else None,
        climatology=climatology,
        note=(
            "Monthly anomalies computed relative to the climatological mean of "
            "each calendar month over the analysed baseline period."
        ),
    )
