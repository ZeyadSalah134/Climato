"""Shared pytest fixtures.

Synthetic series are used to validate the statistical algorithms.  They are
constructed with known properties (exact slope, constant value, injected
gaps, seasonal cycles) so the expected output is analytically defined.
"""

from __future__ import annotations

import math
import os
from datetime import date
from pathlib import Path

# Configure an isolated test environment *before* any application module reads
# settings (settings are cached on first import).
_TMP = Path(__file__).resolve().parent / "_tmp"
_TMP.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("DATABASE_URL", f"sqlite:///{(_TMP / 'test_earthtrend.db').as_posix()}")
os.environ.setdefault("CACHE_DIR", str(_TMP / "cache"))
os.environ.setdefault("DEMO_DATA_DIR", str(_TMP / "samples"))
os.environ.setdefault("CACHE_ENABLED", "false")
os.environ.setdefault("ALLOW_DEMO_FALLBACK", "false")
os.environ.setdefault("RATE_LIMIT_REQUESTS", "1000000")

import pytest  # noqa: E402

from app.core.timeutils import month_end  # noqa: E402
from app.providers.base import ProviderSeries  # noqa: E402
from app.statistics.types import Series  # noqa: E402


def monthly_dates(start_year: int, n_months: int) -> list[date]:
    dates: list[date] = []
    year, month = start_year, 1
    for _ in range(n_months):
        dates.append(month_end(year, month))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return dates


def daily_dates(start: date, n_days: int) -> list[date]:
    return [date.fromordinal(start.toordinal() + i) for i in range(n_days)]


@pytest.fixture
def increasing_series() -> Series:
    """Monthly series rising by exactly 0.05 units per month (0.6 per year)."""
    dates = monthly_dates(2000, 120)
    values = [10.0 + 0.05 * i for i in range(120)]
    return Series(variable="Test Variable", units="degC", dates=dates, values=values, frequency="monthly")


@pytest.fixture
def decreasing_series() -> Series:
    dates = monthly_dates(2000, 120)
    values = [50.0 - 0.02 * i for i in range(120)]
    return Series(variable="Test Variable", units="mm/day", dates=dates, values=values, frequency="monthly")


@pytest.fixture
def constant_series() -> Series:
    dates = monthly_dates(2000, 60)
    values = [7.0] * 60
    return Series(variable="Test Variable", units="m/s", dates=dates, values=values, frequency="monthly")


@pytest.fixture
def noisy_series() -> Series:
    """Series with a known slope and deterministic pseudo-noise."""
    dates = monthly_dates(2000, 120)
    values = [20.0 + 0.03 * i + 1.5 * math.sin(i / 3.0) for i in range(120)]
    return Series(variable="Test Variable", units="degC", dates=dates, values=values, frequency="monthly")


@pytest.fixture
def seasonal_series() -> Series:
    """Strong annual cycle plus a small underlying trend."""
    dates = monthly_dates(2000, 120)
    values = [15.0 + 0.02 * i + 8.0 * math.sin(2 * math.pi * (i % 12) / 12) for i in range(120)]
    return Series(variable="Test Variable", units="degC", dates=dates, values=values, frequency="monthly")


@pytest.fixture
def short_series() -> Series:
    dates = monthly_dates(2023, 6)
    values = [1.0, 1.1, 0.9, 1.2, 1.05, 1.15]
    return Series(variable="Test Variable", units="index", dates=dates, values=values, frequency="monthly")


@pytest.fixture
def irregular_series() -> Series:
    """Series with deliberate month gaps."""
    dates = monthly_dates(2000, 60)
    keep = [i for i in range(60) if i % 7 != 0]
    values = [10.0 + 0.04 * i for i in keep]
    return Series(
        variable="Test Variable",
        units="degC",
        dates=[dates[i] for i in keep],
        values=values,
        frequency="monthly",
    )


class FakePowerProvider:
    """Deterministic provider used to test the API without network access.

    Returns a synthetic, clearly-labelled series.  It is a test double, never
    used in production.
    """

    name = "NASA_POWER"
    community = "SB"

    def __init__(self, slope: float = 0.02, base: float = 20.0, n_months: int = 120) -> None:
        self.slope = slope
        self.base = base
        self.n_months = n_months
        self.calls: list[dict] = []

    async def fetch_series(
        self,
        *,
        variable_code: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        frequency: str,
    ) -> ProviderSeries:
        self.calls.append(
            {
                "variable_code": variable_code,
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date,
                "end_date": end_date,
                "frequency": frequency,
            }
        )
        dates = monthly_dates(start_date.year, self.n_months)
        observations = [(d, self.base + self.slope * i) for i, d in enumerate(dates)]
        return ProviderSeries(
            variable_code=variable_code,
            units="C",
            longname="Test Temperature",
            observations=observations,
            missing=[],
            fill_value=-999.0,
            request_url="https://example.invalid/test",
            request_params={"synthetic": True},
            source_name="synthetic_test_fixture",
            api_version="test",
            retrieval_mode="live",
            notes=["Synthetic test fixture."],
        )

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def fake_provider() -> FakePowerProvider:
    return FakePowerProvider()
