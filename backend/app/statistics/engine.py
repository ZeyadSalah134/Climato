"""The EarthTrend statistical analysis engine.

The engine is pure with respect to external services: it consumes an already
retrieved :class:`Series` and produces statistical results.  This separation
means every statistical routine can be unit tested without network access.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from app.schemas.analysis import (
    DataQuality,
    DistributionBin,
    Interpretation,
    LinearTrendResult,
    MannKendallResult,
    SeasonalResult,
    TheilSenResult,
    TrendLinePoint,
    Warning,
)
from app.statistics import interpretation as interpretation_module
from app.statistics import linear_trend, mann_kendall, quality as quality_module, seasonality, theil_sen
from app.statistics.types import Series

ENGINE_VERSION = "1.0.0"


@dataclass
class AnalysisComputation:
    quality: DataQuality
    observations: list[dict] = field(default_factory=list)
    trend_line: list[TrendLinePoint] = field(default_factory=list)
    ols: LinearTrendResult | None = None
    mann_kendall: MannKendallResult | None = None
    theil_sen: TheilSenResult | None = None
    seasonal: SeasonalResult | None = None
    distribution: list[DistributionBin] = field(default_factory=list)
    interpretation: Interpretation | None = None
    warnings: list[Warning] = field(default_factory=list)


def _build_distribution(values: np.ndarray, units: str) -> list[DistributionBin]:
    if values.size == 0:
        return []
    if np.allclose(values, values[0]):
        return [DistributionBin(label=f"{values[0]:.3g}", count=int(values.size))]
    counts, edges = np.histogram(values, bins=min(12, max(4, int(np.sqrt(values.size)))))
    bins: list[DistributionBin] = []
    for index, count in enumerate(counts):
        label = f"{edges[index]:.3g} to {edges[index + 1]:.3g}"
        bins.append(DistributionBin(label=label, count=int(count)))
    return bins


def _build_trend_line(series: Series, ols: LinearTrendResult, alpha: float) -> list[TrendLinePoint]:
    fitted, lower, upper = linear_trend.confidence_band(series, alpha=alpha)
    points: list[TrendLinePoint] = []
    for index, moment in enumerate(series.dates):
        points.append(
            TrendLinePoint(
                date=moment,
                observed=float(series.values[index]),
                fitted=float(fitted[index]),
                lower=float(lower[index]),
                upper=float(upper[index]),
            )
        )
    return points


def _build_observations(raw: Series, analysis: Series) -> list[dict]:
    """Raw values plus (when adjusted) the anomaly used for fitting."""
    records: list[dict] = []
    for index, moment in enumerate(raw.dates):
        record: dict = {"date": moment.isoformat(), "value": float(raw.values[index])}
        if analysis is not raw:
            record["anomaly"] = float(analysis.values[index])
        records.append(record)
    return records


def run_analysis(
    series: Series,
    *,
    methods: list[str],
    alpha: float = 0.05,
    seasonal_adjustment: bool = False,
    n_missing: int = 0,
    requested_start=None,
    requested_end=None,
    provider_notes: list[str] | None = None,
    units: str | None = None,
) -> AnalysisComputation:
    """Run the full statistical analysis for a retrieved series."""
    units = units or series.units
    quality = quality_module.assess_quality(
        series,
        n_missing=n_missing,
        requested_start=requested_start,
        requested_end=requested_end,
    )

    warnings: list[Warning] = [
        Warning(code="quality", message=message, severity="warning") for message in quality.warnings
    ]
    for note in provider_notes or []:
        warnings.append(Warning(code="provider", message=note, severity="info"))

    analysis_series = series
    seasonal_result: SeasonalResult | None = None
    if seasonal_adjustment:
        analysis_series, seasonal_result = seasonality.apply_seasonal_adjustment(series)
        if seasonal_result.applied:
            warnings.append(
                Warning(
                    code="seasonal_adjustment",
                    message=seasonal_result.note,
                    severity="info",
                )
            )
    else:
        seasonal_result = seasonality.SeasonalResult(
            applied=False,
            note="Seasonal adjustment disabled.",
        )
        if series.frequency == "monthly":
            seasonal_result.climatology = seasonality.compute_climatology(series)

    computation = AnalysisComputation(
        quality=quality,
        seasonal=seasonal_result,
        observations=_build_observations(series, analysis_series),
    )

    if not quality.sufficient:
        computation.warnings = warnings
        computation.warnings.append(
            Warning(
                code="insufficient_data",
                message=(
                    "The series does not meet the minimum data requirements for trend "
                    "analysis. Statistical results were not produced."
                ),
                severity="critical",
            )
        )
        computation.interpretation = interpretation_module.build_interpretation(
            variable_name=series.variable,
            units=units,
            frequency=series.frequency,
            quality=quality,
            ols=None,
            mann_kendall=None,
            theil_sen=None,
            alpha=alpha,
            seasonal_applied=bool(seasonal_result and seasonal_result.applied),
        )
        return computation

    if "ols" in methods:
        computation.ols = linear_trend.compute_linear_trend(analysis_series, alpha=alpha)
        computation.trend_line = _build_trend_line(analysis_series, computation.ols, alpha)

    if "mann_kendall" in methods:
        computation.mann_kendall = mann_kendall.compute_mann_kendall(analysis_series, alpha=alpha)
        if computation.mann_kendall.autocorrelation_risk:
            warnings.append(
                Warning(
                    code="autocorrelation",
                    message=computation.mann_kendall.note,
                    severity="warning",
                )
            )

    if "theil_sen" in methods:
        computation.theil_sen = theil_sen.compute_theil_sen(analysis_series, alpha=alpha)

    computation.distribution = _build_distribution(series.values, units)

    computation.interpretation = interpretation_module.build_interpretation(
        variable_name=series.variable,
        units=units,
        frequency=series.frequency,
        quality=quality,
        ols=computation.ols,
        mann_kendall=computation.mann_kendall,
        theil_sen=computation.theil_sen,
        alpha=alpha,
        seasonal_applied=bool(seasonal_result and seasonal_result.applied),
    )

    computation.warnings = warnings
    return computation
