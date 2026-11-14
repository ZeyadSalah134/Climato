"""Location search schemas."""

from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import GeoPoint


class LocationResult(GeoPoint):
    display_name: str
    feature_type: str | None = None


class LocationSearchResponse(BaseModel):
    query: str
    results: list[LocationResult]
    source: str
