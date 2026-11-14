"""NASA POWER parsing and request-construction tests."""

from __future__ import annotations

from datetime import date

import pytest

from app.core.errors import ProviderError
from app.providers.nasa_power import NasaPowerProvider

MONTHLY_PAYLOAD = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [31.236, 30.044, 135.44]},
    "properties": {
        "parameter": {
            "T2M": {
                "201001": 14.54,
                "201002": 16.56,
                "201012": 15.47,
                "201013": 23.1,  # annual mean -> must be excluded
            },
            "PRECTOTCORR": {
                "201001": 0.06,
                "201002": -999.0,  # fill value -> missing
            },
        }
    },
    "header": {
        "title": "NASA/POWER Source Native Resolution Monthly and Annual",
        "api": {"version": "v2.10.0", "name": "POWER Monthly and Annual API"},
        "sources": ["MERRA2"],
        "fill_value": -999.0,
        "start": "20100101",
        "end": "20101231",
    },
    "messages": [],
    "parameters": {
        "T2M": {"units": "C", "longname": "Temperature at 2 Meters"},
        "PRECTOTCORR": {"units": "mm/day", "longname": "Precipitation Corrected"},
    },
    "times": {"data": 0.121, "process": 0.01},
}

DAILY_PAYLOAD = {
    "header": {"fill_value": -999.0, "sources": ["MERRA2"], "api": {"version": "v2.10.3"}},
    "parameters": {"T2M": {"units": "C", "longname": "Temperature at 2 Meters"}},
    "properties": {
        "parameter": {
            "T2M": {
                "20100101": 16.6,
                "20100102": 16.74,
                "20100103": -999.0,
            }
        }
    },
}


@pytest.fixture
def provider() -> NasaPowerProvider:
    return NasaPowerProvider(base_url="https://power.larc.nasa.gov/api/temporal")


def test_monthly_parsing_excludes_annual_mean(provider: NasaPowerProvider) -> None:
    series = provider._parse(
        MONTHLY_PAYLOAD, "T2M", "monthly", "url", {"parameters": "T2M"}
    )
    assert series.units == "C"
    assert series.longname == "Temperature at 2 Meters"
    assert len(series.observations) == 3
    dates = [d for d, _ in series.observations]
    assert dates == [date(2010, 1, 31), date(2010, 2, 28), date(2010, 12, 31)]
    # Month 13 must not appear.
    assert all(d.month != 1 or d.day == 31 for d in dates)
    assert date(2010, 12, 31) in dates


def test_monthly_parsing_records_missing(provider: NasaPowerProvider) -> None:
    series = provider._parse(
        MONTHLY_PAYLOAD, "PRECTOTCORR", "monthly", "url", {"parameters": "PRECTOTCORR"}
    )
    assert len(series.observations) == 1
    assert series.missing == [date(2010, 2, 28)]
    assert series.fill_value == -999.0


def test_daily_parsing(provider: NasaPowerProvider) -> None:
    series = provider._parse(DAILY_PAYLOAD, "T2M", "daily", "url", {"parameters": "T2M"})
    assert len(series.observations) == 2
    assert series.missing == [date(2010, 1, 3)]
    assert series.observations[0] == (date(2010, 1, 1), 16.6)


def test_unknown_parameter_raises(provider: NasaPowerProvider) -> None:
    with pytest.raises(ProviderError):
        provider._parse(MONTHLY_PAYLOAD, "NOT_A_PARAM", "monthly", "url", {})


def test_build_params_monthly(provider: NasaPowerProvider) -> None:
    params = provider._build_params(
        variable_code="T2M",
        latitude=30.0444,
        longitude=31.2357,
        start_date=date(2010, 1, 1),
        end_date=date(2024, 12, 31),
        frequency="monthly",
    )
    assert params["start"] == "201001"
    assert params["end"] == "202412"
    assert params["latitude"] == "30.0444"
    assert params["longitude"] == "31.2357"
    assert params["format"] == "JSON"


def test_build_params_daily(provider: NasaPowerProvider) -> None:
    params = provider._build_params(
        variable_code="T2M",
        latitude=0.0,
        longitude=0.0,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31),
        frequency="daily",
    )
    assert params["start"] == "20200101"
    assert params["end"] == "20201231"


def test_parse_key_handles_invalid(provider: NasaPowerProvider) -> None:
    assert provider._parse_key("garbage", "monthly") is None
    assert provider._parse_key("201099", "monthly") is None
    assert provider._parse_key("201001", "monthly") == date(2010, 1, 31)
    assert provider._parse_key("201002", "monthly") == date(2010, 2, 28)
    assert provider._parse_key("202002", "monthly") == date(2020, 2, 29)
