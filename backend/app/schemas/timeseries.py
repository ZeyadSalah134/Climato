"""Time-series request/response schemas."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.common import GeoPoint


class TimeSeriesRequest(BaseModel):
    variable: str
    source: str = "NASA_POWER"
    location: GeoPoint
    start_date: date
    end_date: date
    frequency: Literal["monthly", "daily"] = "monthly"

    @model_validator(mode="after")
    def _check_range(self) -> "TimeSeriesRequest":
        if self.end_date <= self.start_date:
            raise ValueError("end_date must be after start_date")
        return self


class Observation(BaseModel):
    date: date
    value: float
    unit: str


class MissingObservation(BaseModel):
    date: date
    reason: str = "provider_missing_value"


class TimeSeriesResponse(BaseModel):
    variable: str
    variable_name: str
    units: str
    location: GeoPoint
    frequency: str
    observations: list[Observation]
    missing: list[MissingObservation]
    n_observations: int
    n_missing: int
    provider: str
    dataset: str
    retrieval_mode: Literal["live", "cache", "demo", "mixed", "dataset"]
    spatial_resolution: str
    warnings: list[str] = Field(default_factory=list)
