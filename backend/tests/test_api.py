"""API integration tests using a deterministic fake provider.

No network access is required: the NASA POWER provider is replaced with a
synthetic test double so results are reproducible in CI.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.timeseries_service import timeseries_service

TREND_REQUEST = {
    "variable": "T2M",
    "source": "NASA_POWER",
    "location": {"latitude": 30.0444, "longitude": 31.2357, "name": "Cairo, Egypt"},
    "start_date": "2010-01-01",
    "end_date": "2020-12-31",
    "frequency": "monthly",
    "methods": ["ols", "mann_kendall", "theil_sen"],
    "seasonal_adjustment": False,
    "alpha": 0.05,
}


@pytest.fixture
def client(fake_provider, monkeypatch):
    monkeypatch.setattr(timeseries_service, "provider", fake_provider)
    with TestClient(app) as test_client:
        yield test_client


def test_health(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["engine_version"]


def test_root(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "EarthTrend" in response.json()["name"]


def test_openapi_document(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/analysis/trend" in paths
    assert "/api/v1/variables" in paths


def test_list_variables(client: TestClient) -> None:
    response = client.get("/api/v1/variables")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 5
    ids = {item["id"] for item in body["items"]}
    assert "T2M" in ids


def test_available_only_filter(client: TestClient) -> None:
    response = client.get("/api/v1/variables", params={"available_only": True})
    assert response.status_code == 200
    assert all(item["status"] == "available" for item in response.json()["items"])


def test_variable_detail(client: TestClient) -> None:
    response = client.get("/api/v1/variables/T2M")
    assert response.status_code == 200
    assert response.json()["units"] == "degC"


def test_unknown_variable_returns_400(client: TestClient) -> None:
    response = client.get("/api/v1/variables/NOT_A_VARIABLE")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_variable"


def test_planned_variable_cannot_be_analysed(client: TestClient) -> None:
    payload = dict(TREND_REQUEST)
    payload["variable"] = "MODIS_NDVI"
    response = client.post("/api/v1/analysis/trend", json=payload)
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "unsupported_variable"


def test_discover(client: TestClient) -> None:
    response = client.post("/api/v1/variables/discover", json={"question": "Is it getting warmer?"})
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"][0]["variable"]["id"] == "T2M"


def test_location_search_falls_back_offline(client: TestClient, monkeypatch) -> None:
    import httpx

    async def boom(*args, **kwargs):
        raise httpx.ConnectError("offline")

    monkeypatch.setattr(httpx.AsyncClient, "get", boom)
    response = client.get("/api/v1/locations/search", params={"q": "Cairo"})
    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "offline_gazetteer"
    assert body["results"][0]["latitude"] == pytest.approx(30.0444, abs=0.001)


def test_timeseries_endpoint(client: TestClient) -> None:
    response = client.post(
        "/api/v1/data/timeseries",
        json={
            "variable": "T2M",
            "location": {"latitude": 30.0444, "longitude": 31.2357},
            "start_date": "2010-01-01",
            "end_date": "2020-12-31",
            "frequency": "monthly",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["n_observations"] == 120
    assert body["units"] == "C"
    assert body["variable_name"] == "Air Temperature"


def test_trend_analysis_endpoint(client: TestClient) -> None:
    response = client.post("/api/v1/analysis/trend", json=TREND_REQUEST)
    assert response.status_code == 200
    body = response.json()

    assert body["analysis_id"]
    assert body["ols"]["slope_per_year"] > 0
    assert body["ols"]["significant"] is True
    assert body["mann_kendall"]["trend"] == "increasing"
    assert body["theil_sen"]["slope_per_year"] > 0
    assert len(body["trend_line"]) == 120
    assert body["quality"]["sufficient"] is True
    assert body["provenance"]["variable"] == "T2M"
    assert body["interpretation"]["narrative"]
    assert body["request"]["location"]["name"] == "Cairo, Egypt"


def test_trend_validation_error(client: TestClient) -> None:
    payload = dict(TREND_REQUEST)
    payload["end_date"] = "2009-01-01"  # before start
    response = client.post("/api/v1/analysis/trend", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_invalid_coordinates_rejected(client: TestClient) -> None:
    payload = dict(TREND_REQUEST)
    payload["location"] = {"latitude": 200.0, "longitude": 0.0}
    response = client.post("/api/v1/analysis/trend", json=payload)
    assert response.status_code == 422


def test_retrieve_and_history(client: TestClient) -> None:
    created = client.post("/api/v1/analysis/trend", json=TREND_REQUEST).json()
    analysis_id = created["analysis_id"]

    fetched = client.get(f"/api/v1/analysis/{analysis_id}")
    assert fetched.status_code == 200
    assert fetched.json()["analysis_id"] == analysis_id

    history = client.get("/api/v1/analysis/history")
    assert history.status_code == 200
    assert history.json()["total"] >= 1

    missing = client.get("/api/v1/analysis/does-not-exist")
    assert missing.status_code == 404


def test_compare_endpoint(client: TestClient) -> None:
    payload = {
        "variable": "T2M",
        "location_a": {"latitude": 30.0444, "longitude": 31.2357, "name": "Cairo"},
        "location_b": {"latitude": -3.119, "longitude": -60.0217, "name": "Manaus"},
        "start_date": "2010-01-01",
        "end_date": "2020-12-31",
        "frequency": "monthly",
    }
    response = client.post("/api/v1/analysis/compare", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["comparison"]["descriptive_only"] is True
    assert "statistically significant" in body["comparison"]["note"]
    assert body["location_a"]["ols"] is not None
    assert body["location_b"]["ols"] is not None


def test_export_formats(client: TestClient) -> None:
    created = client.post("/api/v1/analysis/trend", json=TREND_REQUEST).json()
    analysis_id = created["analysis_id"]

    csv_response = client.get(f"/api/v1/export/{analysis_id}", params={"format": "csv"})
    assert csv_response.status_code == 200
    assert "text/csv" in csv_response.headers["content-type"]
    assert "observed_value" in csv_response.text

    json_response = client.get(f"/api/v1/export/{analysis_id}", params={"format": "json"})
    assert json_response.status_code == 200
    assert json_response.json()["analysis_id"] == analysis_id

    pdf_response = client.get(f"/api/v1/export/{analysis_id}", params={"format": "pdf"})
    assert pdf_response.status_code == 200
    assert pdf_response.content[:4] == b"%PDF"


def test_dataset_endpoints(client: TestClient) -> None:
    datasets = client.get("/api/v1/datasets")
    assert datasets.status_code == 200
    ids = {item["id"] for item in datasets.json()["items"]}
    assert "NASA_POWER" in ids

    demo = client.get("/api/v1/datasets/demo")
    assert demo.status_code == 200

    geo = client.get("/api/v1/datasets/geospatial")
    assert geo.status_code == 200


def test_geospatial_context_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/locations/context", params={"latitude": 30.0, "longitude": 31.0})
    assert response.status_code == 200
    body = response.json()
    assert body["latitude"] == 30.0
