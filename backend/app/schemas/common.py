"""Shared response primitives."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class GeoPoint(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Decimal degrees, WGS84")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Decimal degrees, WGS84")
    name: str | None = Field(default=None, description="Optional human readable label")
    country: str | None = None
    region: str | None = None


class GeoBounds(BaseModel):
    """A geographic bounding box for regional extraction."""

    min_latitude: float = Field(..., ge=-90.0, le=90.0)
    max_latitude: float = Field(..., ge=-90.0, le=90.0)
    min_longitude: float = Field(..., ge=-180.0, le=180.0)
    max_longitude: float = Field(..., ge=-180.0, le=180.0)


class DataProvenance(BaseModel):
    """Reproducibility metadata attached to every scientific result."""

    variable: str
    variable_name: str
    units: str
    provider: str
    dataset: str
    product_type: Literal[
        "satellite_observation",
        "model_estimate",
        "reanalysis",
        "reference_dataset",
        "derived_statistic",
    ]
    spatial_resolution: str
    source_url: str
    request_params: dict[str, Any] = Field(default_factory=dict)
    requested_start: str
    requested_end: str
    analyzed_start: str | None = None
    analyzed_end: str | None = None
    frequency: str
    retrieval_mode: Literal["live", "cache", "demo", "mixed", "dataset"] = "live"
    retrieved_at: datetime
    engine_version: str


class Warning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "critical"] = "warning"


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    engine_version: str
    environment: str
    cache_enabled: bool
    database: str
    provider_reachable: bool | None = None
    timestamp: datetime


class Paginated(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
