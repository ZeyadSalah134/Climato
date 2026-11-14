"""Location search and geospatial context endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query

from app.geospatial.raster_context import get_context
from app.schemas.location import LocationSearchResponse
from app.services.location_service import search_locations

router = APIRouter(tags=["locations"])


@router.get("/locations/search", response_model=LocationSearchResponse, summary="Search for a location")
async def location_search(
    q: str = Query(..., min_length=1, max_length=200, description="Free-text place name"),
    limit: int = Query(default=8, ge=1, le=25),
) -> LocationSearchResponse:
    return await search_locations(q, limit=limit)


@router.get("/locations/context", summary="Static geographic context for a coordinate")
async def location_context(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
) -> dict:
    """Return optional elevation / land-cover context.

    These are static reference values and never a time series.
    """
    context = get_context(latitude, longitude)
    return context.__dict__
