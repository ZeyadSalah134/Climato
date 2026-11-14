"""Export service tests (CSV, JSON, PDF) built from real computed results."""

from __future__ import annotations

import pytest

from app.exports import build_csv, build_json, build_pdf
from app.schemas.analysis import TrendRequest
from app.services.analysis_service import analysis_service
from app.services.timeseries_service import timeseries_service


async def _make_response(fake_provider, monkeypatch):
    monkeypatch.setattr(timeseries_service, "provider", fake_provider)
    request = TrendRequest(
        variable="T2M",
        location={"latitude": 30.0444, "longitude": 31.2357, "name": "Cairo, Egypt"},
        start_date="2010-01-01",
        end_date="2020-12-31",
        frequency="monthly",
        methods=["ols", "mann_kendall", "theil_sen"],
    )
    return await analysis_service.run_trend(request, allow_demo=False)


async def test_csv_export_contains_provenance(fake_provider, monkeypatch) -> None:
    response = await _make_response(fake_provider, monkeypatch)
    csv = build_csv(response)
    assert "# variable" in csv
    assert "T2M" in csv
    assert "observed_value" in csv
    assert "fitted_value" in csv
    # One header line + one row per observation.
    data_lines = [line for line in csv.splitlines() if line and not line.startswith("#")]
    assert len(data_lines) >= response.quality.n_valid


async def test_json_export_round_trips(fake_provider, monkeypatch) -> None:
    response = await _make_response(fake_provider, monkeypatch)
    payload = build_json(response)
    assert '"analysis_id"' in payload
    assert response.analysis_id in payload


async def test_pdf_export_is_valid_pdf(fake_provider, monkeypatch) -> None:
    pytest.importorskip("reportlab")
    response = await _make_response(fake_provider, monkeypatch)
    pdf = build_pdf(response)
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 1000
