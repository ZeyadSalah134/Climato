"""Test Climato verified project dataset integration."""

from datetime import date
import pytest
from app.services.climate_dataset_service import climate_dataset_service, load_verified_stations
from app.services.timeseries_service import timeseries_service


def test_verified_stations_loaded():
    stations = load_verified_stations()
    assert len(stations) == 30
    cairo_station = [s for s in stations if "Cairo" in s.name]
    assert len(cairo_station) >= 1


@pytest.mark.asyncio
async def test_timeseries_retrieves_cairo_dataset():
    # Cairo coordinates
    bundle = await timeseries_service.get_series(
        variable="T2M",
        latitude=30.0444,
        longitude=31.2357,
        start_date=date(2000, 1, 1),
        end_date=date(2025, 12, 1),
        frequency="monthly",
    )
    assert bundle.retrieval_mode == "dataset"
    assert len(bundle.series.values) == 312  # 26 years * 12 months
    assert bundle.series.variable == "Air Temperature"
    assert bundle.series.units == "degC"
