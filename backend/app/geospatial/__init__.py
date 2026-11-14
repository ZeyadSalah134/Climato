"""Optional geospatial context module."""

from app.geospatial.raster_context import (
    WORLDCOVER_CLASSES,
    GeospatialContext,
    RasterInfo,
    get_context,
    inspect_raster,
)

__all__ = ["WORLDCOVER_CLASSES", "GeospatialContext", "RasterInfo", "get_context", "inspect_raster"]
