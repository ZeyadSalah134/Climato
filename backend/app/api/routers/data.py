"""Raw time-series retrieval endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.deps import get_allow_demo, rate_limit
from app.schemas.timeseries import (
    MissingObservation,
    Observation,
    TimeSeriesRequest,
    TimeSeriesResponse,
)
from app.services.timeseries_service import timeseries_service
from app.services.variable_registry import get_variable

router = APIRouter(tags=["data"], dependencies=[Depends(rate_limit)])


@router.post("/data/timeseries", response_model=TimeSeriesResponse, summary="Retrieve an observation series")
async def get_timeseries(
    request: TimeSeriesRequest,
    allow_demo: bool = Depends(get_allow_demo),
) -> TimeSeriesResponse:
    definition = get_variable(request.variable, require_available=True)
    bundle = await timeseries_service.get_series(
        variable=request.variable,
        latitude=request.location.latitude,
        longitude=request.location.longitude,
        start_date=request.start_date,
        end_date=request.end_date,
        frequency=request.frequency,
        allow_demo=allow_demo,
    )
    provider_series = bundle.provider_series
    units = provider_series.units or definition.units

    observations = [
        Observation(date=moment, value=value, unit=units) for moment, value in provider_series.observations
    ]
    missing = [MissingObservation(date=moment) for moment in provider_series.missing]

    return TimeSeriesResponse(
        variable=definition.id,
        variable_name=definition.display_name,
        units=units,
        location=request.location,
        frequency=request.frequency,
        observations=observations,
        missing=missing,
        n_observations=len(observations),
        n_missing=len(missing),
        provider=definition.provider,
        dataset=definition.dataset,
        retrieval_mode=bundle.retrieval_mode,  # type: ignore[arg-type]
        spatial_resolution=definition.spatial_resolution,
        warnings=bundle.warnings,
    )
