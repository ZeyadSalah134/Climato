"""Generate human-readable scientific interpretation from computed results.

Every sentence produced here is derived from actual numeric outputs.  No
conclusion is hard-coded and non-significant results are never described as
proof that no change exists.
"""

from __future__ import annotations

from app.schemas.analysis import (
    DataQuality,
    Interpretation,
    LinearTrendResult,
    MannKendallResult,
    TheilSenResult,
)


def _fmt(value: float, sig: int = 3) -> str:
    if value == 0:
        return "0"
    magnitude = abs(value)
    if magnitude >= 1000 or magnitude < 0.001:
        return f"{value:.{sig}g}"
    return f"{value:.{sig}g}"


def _fmt_p(p: float) -> str:
    if p < 0.0001:
        return "< 0.0001"
    return f"{p:.4f}"


def _direction_word(direction: str) -> str:
    return {
        "increasing": "increasing",
        "decreasing": "decreasing",
        "no_detectable_trend": "no statistically detectable",
    }.get(direction, direction)


def build_interpretation(
    *,
    variable_name: str,
    units: str,
    frequency: str,
    quality: DataQuality,
    ols: LinearTrendResult | None,
    mann_kendall: MannKendallResult | None,
    theil_sen: TheilSenResult | None,
    alpha: float,
    seasonal_applied: bool,
) -> Interpretation:
    limitations = _limitations(quality, frequency, seasonal_applied)

    if ols is None or quality.period_start is None or quality.period_end is None:
        return Interpretation(
            headline="Analysis could not be completed",
            narrative=(
                "The available observations did not support a linear trend estimate. "
                "See the data quality report for details."
            ),
            significance_statement="No significance test was performed.",
            practical_note="Interpretation requires a successful trend estimate.",
            limitations=limitations,
        )

    period = f"{quality.period_start.isoformat()} to {quality.period_end.isoformat()}"
    direction = ols.direction
    slope = ols.slope_per_year
    decade = ols.slope_per_decade
    unit_year = f"{units}/year" if units else "units/year"

    if direction == "no_detectable_trend":
        headline = f"No statistically detectable trend in {variable_name}"
    elif direction == "increasing":
        headline = f"{variable_name} is increasing"
    else:
        headline = f"{variable_name} is decreasing"

    seasonal_note = (
        " Seasonal adjustment was applied, so the trend describes change beyond "
        "the normal seasonal cycle."
        if seasonal_applied
        else ""
    )

    narrative = (
        f"During the selected observation period ({period}), {variable_name} showed an "
        f"estimated {_direction_word(direction)} trend of {_fmt(slope)} {unit_year} "
        f"({_fmt(decade)} {units}/decade). The ordinary least squares regression returned "
        f"p = {_fmt_p(ols.p_value)} with an R-squared of {ols.r_squared:.2f}, over "
        f"{ols.n_observations} valid observations.{seasonal_note}"
    )

    if ols.significant:
        significance_statement = (
            f"At the selected significance threshold (alpha = {alpha:g}), this result provides "
            f"sufficient evidence of a monotonic or linear trend: p = {_fmt_p(ols.p_value)} is "
            f"below the threshold. The 95% confidence interval for the slope is "
            f"[{_fmt(ols.confidence_interval_95[0])}, {_fmt(ols.confidence_interval_95[1])}] {unit_year}."
        )
    else:
        significance_statement = (
            f"At the selected significance threshold (alpha = {alpha:g}), this result does not "
            f"provide sufficient evidence to reject the null hypothesis of no trend "
            f"(p = {_fmt_p(ols.p_value)}). This is not evidence that no change occurred; it means "
            "the observed change is not distinguishable from natural variability given the data."
        )

    if mann_kendall is not None:
        significance_statement += (
            f" The non-parametric Mann-Kendall test reported tau = {mann_kendall.tau:.3f} "
            f"and p = {_fmt_p(mann_kendall.p_value)}, indicating a "
            f"{mann_kendall.trend.replace('_', ' ')} result."
        )
    if theil_sen is not None:
        significance_statement += (
            f" The robust Theil-Sen slope estimate is {_fmt(theil_sen.slope_per_year)} {unit_year}."
        )

    practical_note = (
        "Statistical significance describes whether an observed change is unlikely to arise from "
        "random variability alone. It is not the same as environmental or practical importance. "
        f"A slope of {_fmt(slope)} {unit_year} may be physically small or large depending on the "
        "variable, the ecosystem, and the decision context. Practical importance should be judged "
        "against domain knowledge and the measurement uncertainty of the source product."
    )

    return Interpretation(
        headline=headline,
        narrative=narrative,
        significance_statement=significance_statement,
        practical_note=practical_note,
        limitations=limitations,
    )


def _limitations(quality: DataQuality, frequency: str, seasonal_applied: bool) -> list[str]:
    limitations = [
        "Correlation does not imply causation: a detected trend describes co-variation with time, "
        "not a proven causal mechanism.",
        "Values represent the source grid cell rather than an exact point measurement; local "
        "microclimate may differ from the analysed cell.",
    ]
    if quality.n_missing > 0:
        limitations.append(
            f"{quality.n_missing} expected observation(s) were missing and excluded from the analysis."
        )
    if quality.period_years < 10:
        limitations.append(
            "The analysed period is shorter than ten years; longer records are needed to separate "
            "long-term climate signals from multi-year variability."
        )
    if quality.autocorrelation_warning:
        limitations.append(
            "Serial autocorrelation was detected, which can make significance estimates optimistic."
        )
    if quality.irregular_sampling:
        limitations.append("The record contains gaps, so sampling is not perfectly regular.")
    if frequency == "monthly" and not seasonal_applied:
        limitations.append(
            "Seasonal adjustment was not applied. For strongly seasonal variables the trend may "
            "partly reflect seasonal cycle amplitude."
        )
    if frequency == "daily":
        limitations.append(
            "Daily data contain strong short-term autocorrelation; interpret significance with care."
        )
    return limitations
