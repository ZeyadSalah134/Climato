"""Dataset catalogue and demonstration-snapshot endpoints."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.config import settings
from app.geospatial.raster_context import inspect_raster
from app.services import demo_store
from app.services.variable_registry import list_variables

router = APIRouter(tags=["datasets"])


@router.get("/datasets", summary="List data sources and adapters")
async def list_datasets() -> dict[str, Any]:
    """Describe every data provider adapter and its integration status."""
    return {
        "items": [
            {
                "id": "NASA_POWER",
                "name": "NASA POWER",
                "provider": "NASA Langley Research Center",
                "status": "available",
                "product_type": "reanalysis",
                "documentation": "https://power.larc.nasa.gov/docs/services/api/temporal/",
                "temporal_endpoints": ["monthly", "daily"],
                "community": settings.power_community,
                "description": (
                    "Prediction Of Worldwide Energy Resources. Provides solar and "
                    "meteorological parameters on a regular grid, derived from MERRA-2 "
                    "and CERES with bias correction."
                ),
                "variables": [v.id for v in list_variables(include_planned=False)],
            },
            {
                "id": "GES_DISC",
                "name": "NASA GES DISC",
                "provider": "NASA Goddard Earth Sciences Data and Information Services Center",
                "status": "planned_integration",
                "product_type": "satellite_observation",
                "documentation": "https://disc.gsfc.nasa.gov/",
                "description": (
                    "GPM IMERG precipitation, MERRA-2 aerosol, GLDAS land surface, AIRS "
                    "temperature and OMI composition products. Adapters are designed but "
                    "require verified Earthdata authentication before activation."
                ),
                "variables": [v.id for v in list_variables() if v.supported_by == "GES_DISC"],
            },
            {
                "id": "LP_DAAC",
                "name": "NASA LP DAAC",
                "provider": "NASA Land Processes Distributed Active Archive Center",
                "status": "planned_integration",
                "product_type": "satellite_observation",
                "documentation": "https://lpdaac.usgs.gov/",
                "description": (
                    "MODIS vegetation and land products. Adapter designed for windowed "
                    "GeoTIFF/NetCDF extraction pending verified authentication."
                ),
                "variables": [v.id for v in list_variables() if v.supported_by == "LP_DAAC"],
            },
        ]
    }


@router.get("/datasets/demo", summary="List bundled demonstration snapshots")
async def list_demo_datasets() -> dict[str, Any]:
    """List real, previously retrieved NASA POWER snapshots available offline."""
    samples = demo_store.list_samples()
    return {
        "enabled": settings.allow_demo_fallback,
        "count": len(samples),
        "items": [sample.to_public() for sample in samples],
        "note": (
            "Demonstration snapshots are real NASA POWER responses captured on the "
            "recorded retrieval date. They are used only when live retrieval is "
            "unavailable, and results are always labelled retrieval_mode='demo'."
        ),
    }


@router.get("/datasets/verified", summary="List verified Climato project dataset stations")
async def list_verified_dataset() -> dict[str, Any]:
    """Return stations and coverage of the verified 2000-2025 monthly NASA POWER dataset."""
    from app.services.climate_dataset_service import load_verified_stations, get_dataset_csv_path
    stations = load_verified_stations()
    csv_path = get_dataset_csv_path()
    return {
        "available": bool(csv_path and csv_path.exists()),
        "dataset_name": "Climato NASA POWER Monthly Observations (2000-2025)",
        "source": "NASA POWER Agroclimatology (AG, monthly)",
        "coverage": {
            "period": "2000-01 to 2025-12 (312 months)",
            "region": "Egypt / Nile Delta / Suez Canal / Middle Nile",
            "latitudes": [29.5, 30.0, 30.5, 31.0, 31.5],
            "longitudes": [29.375, 30.0, 30.625, 31.25, 31.875, 32.5],
        },
        "variables": [
            {"code": "T2M", "name": "Air Temperature", "units": "degC"},
            {"code": "PRECTOTCORR", "name": "Precipitation", "units": "mm/day"},
            {"code": "ALLSKY_SFC_SW_DWN", "name": "Solar Radiation", "units": "MJ/m^2/day"},
        ],
        "total_observations": 28080,
        "stations_count": len(stations),
        "stations": [
            {
                "point_id": s.point_id,
                "name": s.name,
                "latitude": s.latitude,
                "longitude": s.longitude,
            }
            for s in stations
        ],
    }


@router.get("/datasets/geospatial", summary="Geospatial reference dataset status")
async def geospatial_status() -> dict[str, Any]:
    """Report whether optional local rasters are configured and readable."""
    from pathlib import Path

    result: dict[str, Any] = {"enabled": settings.geospatial_enabled, "rasters": []}
    for product, path in (
        ("NASADEM", settings.nasadem_path),
        ("ESA WorldCover", settings.worldcover_path),
    ):
        if path:
            info = inspect_raster(Path(path), product)
            result["rasters"].append(info.__dict__)
        else:
            result["rasters"].append(
                {
                    "available": False,
                    "product": product,
                    "path": None,
                    "note": "Not configured. Set the corresponding environment variable to enable.",
                }
            )
    result["note"] = (
        "NASADEM and ESA WorldCover are static reference datasets. They provide geographic "
        "context only and cannot establish a temporal environmental trend."
    )
    return result
