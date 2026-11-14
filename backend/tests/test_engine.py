"""Analysis engine and interpretation tests."""

from __future__ import annotations

from app.statistics import run_analysis
from app.statistics.types import Series


def test_run_analysis_full_pipeline(increasing_series: Series) -> None:
    computation = run_analysis(
        increasing_series,
        methods=["ols", "mann_kendall", "theil_sen"],
        alpha=0.05,
    )
    assert computation.quality.sufficient is True
    assert computation.ols is not None
    assert computation.mann_kendall is not None
    assert computation.theil_sen is not None
    assert len(computation.trend_line) == increasing_series.n
    assert computation.interpretation is not None
    assert "increasing" in computation.interpretation.headline.lower()
    assert len(computation.distribution) > 0


def test_run_analysis_insufficient_data_returns_no_statistics(short_series: Series) -> None:
    computation = run_analysis(short_series, methods=["ols", "mann_kendall"])
    assert computation.quality.sufficient is False
    assert computation.ols is None
    assert computation.mann_kendall is None
    assert any(warning.code == "insufficient_data" for warning in computation.warnings)
    assert computation.interpretation is not None


def test_interpretation_is_dynamic_and_mentions_units(increasing_series: Series) -> None:
    computation = run_analysis(increasing_series, methods=["ols"])
    narrative = computation.interpretation.narrative
    assert "degC/year" in narrative
    assert "p =" in narrative
    assert "2010" not in narrative  # no fabricated dates


def test_interpretation_non_significant_is_not_proof() -> None:
    from datetime import date

    dates = [date(2000 + i // 12, i % 12 + 1, 28) for i in range(60)]
    values = [10.0 + (0.5 if i % 2 == 0 else -0.5) for i in range(60)]
    series = Series(variable="Noisy", units="u", dates=dates, values=values, frequency="monthly")
    computation = run_analysis(series, methods=["ols"])
    assert computation.ols is not None
    if not computation.ols.significant:
        assert "not evidence that no change occurred" in computation.interpretation.significance_statement


def test_seasonal_adjustment_sets_flag(seasonal_series: Series) -> None:
    computation = run_analysis(
        seasonal_series,
        methods=["ols", "mann_kendall"],
        seasonal_adjustment=True,
    )
    assert computation.seasonal is not None
    assert computation.seasonal.applied is True
    assert len(computation.seasonal.climatology) == 12
    # Observations carry the anomaly used for fitting.
    assert all("anomaly" in record for record in computation.observations)


def test_seasonal_disabled_still_returns_climatology(seasonal_series: Series) -> None:
    computation = run_analysis(seasonal_series, methods=["ols"], seasonal_adjustment=False)
    assert computation.seasonal is not None
    assert computation.seasonal.applied is False
    assert len(computation.seasonal.climatology) == 12


def test_trend_line_has_confidence_band(increasing_series: Series) -> None:
    computation = run_analysis(increasing_series, methods=["ols"])
    for point in computation.trend_line:
        assert point.lower is not None and point.upper is not None
        assert point.lower <= point.fitted <= point.upper
