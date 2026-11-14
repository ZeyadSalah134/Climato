"""Statistical engine tests using deterministic synthetic series."""

from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from app.statistics import linear_trend, mann_kendall, quality, seasonality, theil_sen
from app.statistics.types import Series

# --------------------------------------------------------------------------
# Ordinary least squares
# --------------------------------------------------------------------------


def test_ols_recovers_known_slope(increasing_series: Series) -> None:
    result = linear_trend.compute_linear_trend(increasing_series)
    # Values rise by 0.05 per month => ~0.6 per year.
    assert result.slope_per_year == pytest.approx(0.6, rel=0.01)
    assert result.slope_per_decade == pytest.approx(6.0, rel=0.01)
    assert result.r_squared == pytest.approx(1.0, abs=1e-6)
    assert result.p_value < 1e-6
    assert result.direction == "increasing"
    assert result.significant is True
    assert result.units_per_year == "degC/year"
    assert result.n_observations == 120


def test_ols_decreasing_series(decreasing_series: Series) -> None:
    result = linear_trend.compute_linear_trend(decreasing_series)
    assert result.slope_per_year == pytest.approx(-0.24, rel=0.01)
    assert result.direction == "decreasing"
    assert result.significant is True


def test_ols_constant_series(constant_series: Series) -> None:
    result = linear_trend.compute_linear_trend(constant_series)
    assert result.slope_per_year == 0.0
    assert result.p_value == 1.0
    assert result.direction == "no_detectable_trend"
    assert result.significant is False


def test_ols_matches_scipy_reference(noisy_series: Series) -> None:
    result = linear_trend.compute_linear_trend(noisy_series)
    x = noisy_series.elapsed_years()
    y = noisy_series.values
    reference = stats.linregress(x, y)
    assert result.slope_per_year == pytest.approx(reference.slope)
    assert result.p_value == pytest.approx(reference.pvalue)
    assert result.r_squared == pytest.approx(reference.rvalue**2)


def test_ols_confidence_interval_brackets_slope(noisy_series: Series) -> None:
    result = linear_trend.compute_linear_trend(noisy_series)
    low, high = result.confidence_interval_95
    assert low < result.slope_per_year < high
    assert result.confidence_interval_95_per_decade[0] == pytest.approx(low * 10)


def test_ols_requires_minimum_observations() -> None:
    from datetime import date

    series = Series(
        variable="X",
        units="u",
        dates=[date(2020, 1, 31), date(2020, 2, 29)],
        values=[1.0, 2.0],
        frequency="monthly",
    )
    from app.core.errors import InsufficientDataError

    with pytest.raises(InsufficientDataError):
        linear_trend.compute_linear_trend(series)


def test_confidence_band_shape(noisy_series: Series) -> None:
    fitted, lower, upper = linear_trend.confidence_band(noisy_series)
    assert len(fitted) == len(lower) == len(upper) == noisy_series.n
    assert np.all(lower <= fitted + 1e-9)
    assert np.all(fitted <= upper + 1e-9)


# --------------------------------------------------------------------------
# Mann-Kendall
# --------------------------------------------------------------------------


def test_mann_kendall_increasing(increasing_series: Series) -> None:
    result = mann_kendall.compute_mann_kendall(increasing_series)
    assert result.trend == "increasing"
    assert result.tau == pytest.approx(1.0)
    assert result.p_value < 1e-6
    assert result.significant is True


def test_mann_kendall_decreasing(decreasing_series: Series) -> None:
    result = mann_kendall.compute_mann_kendall(decreasing_series)
    assert result.trend == "decreasing"
    assert result.tau == pytest.approx(-1.0)


def test_mann_kendall_constant(constant_series: Series) -> None:
    result = mann_kendall.compute_mann_kendall(constant_series)
    assert result.s == 0.0
    assert result.trend == "no_detectable_trend"
    assert result.p_value == pytest.approx(1.0)


def test_mann_kendall_tie_correction_is_applied() -> None:
    from datetime import date

    dates = [date(2020, m, 28) for m in range(1, 9)]
    values = [1.0, 1.0, 1.0, 2.0, 2.0, 2.0, 3.0, 3.0]
    series = Series(variable="X", units="u", dates=dates, values=values, frequency="monthly")
    result = mann_kendall.compute_mann_kendall(series)
    # Variance must be reduced by the tie correction relative to the untied value.
    untied = (8 * 7 * (2 * 8 + 5)) / 18
    assert result.variance_s < untied


def test_mann_kendall_matches_pymannkendall(increasing_series: Series) -> None:
    pymannkendall = pytest.importorskip("pymannkendall")
    result = mann_kendall.compute_mann_kendall(increasing_series)
    reference = pymannkendall.original_test(increasing_series.values)
    assert result.tau == pytest.approx(reference.Tau, abs=1e-9)
    assert result.s == pytest.approx(reference.s, abs=1e-9)
    assert result.p_value == pytest.approx(reference.p, abs=1e-9)


# --------------------------------------------------------------------------
# Theil-Sen
# --------------------------------------------------------------------------


def test_theil_sen_recovers_slope(increasing_series: Series) -> None:
    result = theil_sen.compute_theil_sen(increasing_series)
    assert result.slope_per_year == pytest.approx(0.6, rel=0.01)
    assert result.direction == "increasing"


def test_theil_sen_robust_to_outlier() -> None:
    from datetime import date

    dates = [date(2000 + i // 12, i % 12 + 1, 28) for i in range(60)]
    values = [10.0 + 0.1 * i for i in range(60)]
    values[30] = 9999.0  # single gross outlier
    series = Series(variable="X", units="u", dates=dates, values=values, frequency="monthly")
    result = theil_sen.compute_theil_sen(series)
    # Theil-Sen should remain close to the true slope despite the outlier.
    assert result.slope_per_year == pytest.approx(1.2, rel=0.25)


def test_theil_sen_constant(constant_series: Series) -> None:
    result = theil_sen.compute_theil_sen(constant_series)
    assert result.slope_per_year == 0.0


# --------------------------------------------------------------------------
# Seasonality
# --------------------------------------------------------------------------


def test_seasonal_climatology_has_twelve_months(seasonal_series: Series) -> None:
    climatology = seasonality.compute_climatology(seasonal_series)
    assert len(climatology) == 12
    assert {entry.month for entry in climatology} == set(range(1, 13))
    # Each month appears 10 times across 10 years.
    assert all(entry.count == 10 for entry in climatology)


def test_seasonal_adjustment_removes_cycle(seasonal_series: Series) -> None:
    adjusted, result = seasonality.apply_seasonal_adjustment(seasonal_series)
    assert result.applied is True
    # After removing the monthly climatology, the seasonal amplitude collapses.
    monthly_means = [
        np.mean([v for d, v in zip(adjusted.dates, adjusted.values, strict=False) if d.month == m])
        for m in range(1, 13)
    ]
    assert max(monthly_means) - min(monthly_means) < 1e-6
    # The remaining trend is the injected 0.02 per month (~0.24 per year).
    trend = linear_trend.compute_linear_trend(adjusted)
    assert trend.slope_per_year == pytest.approx(0.24, rel=0.02)


def test_seasonal_adjustment_skipped_for_daily() -> None:
    from datetime import date

    dates = [date.fromordinal(date(2020, 1, 1).toordinal() + i) for i in range(400)]
    values = [float(i % 7) for i in range(400)]
    series = Series(variable="X", units="u", dates=dates, values=values, frequency="daily")
    adjusted, result = seasonality.apply_seasonal_adjustment(series)
    assert result.applied is False
    assert adjusted is series


# --------------------------------------------------------------------------
# Quality assessment
# --------------------------------------------------------------------------


def test_quality_flags_insufficient_data(short_series: Series) -> None:
    report = quality.assess_quality(short_series)
    assert report.sufficient is False
    assert report.n_valid == 6
    assert any(check.status == "fail" for check in report.checks)
    assert any("Insufficient" in warning for warning in report.warnings)


def test_quality_flags_constant_series(constant_series: Series) -> None:
    report = quality.assess_quality(constant_series)
    assert report.is_constant is True
    assert any(check.name == "variance" and check.status == "warning" for check in report.checks)


def test_quality_detects_irregular_sampling(irregular_series: Series) -> None:
    report = quality.assess_quality(irregular_series)
    assert report.irregular_sampling is True


def test_quality_missing_percentage() -> None:
    from datetime import date

    dates = [date(2000 + i // 12, i % 12 + 1, 28) for i in range(60)]
    values = [float(i) for i in range(60)]
    series = Series(variable="X", units="u", dates=dates, values=values, frequency="monthly")
    report = quality.assess_quality(series, n_missing=10)
    assert report.n_missing == 10
    assert report.missing_pct == pytest.approx(100 * 10 / 70, rel=0.01)


def test_quality_flags_high_autocorrelation() -> None:
    from datetime import date

    dates = [date(2000 + i // 12, i % 12 + 1, 28) for i in range(120)]
    # Strong smooth oscillation produces high residual autocorrelation.
    values = [np.sin(i / 6.0) * 10 + i * 0.001 for i in range(120)]
    series = Series(variable="X", units="u", dates=dates, values=values, frequency="monthly")
    report = quality.assess_quality(series)
    assert report.autocorrelation_warning is True
