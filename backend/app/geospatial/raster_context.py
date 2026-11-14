"""Optional geospatial context from local raster products.

Two prepared static reference datasets can be inspected and sampled when they
are present in the workspace:

* **NASADEM** digital elevation model (GeoTIFF).
* **ESA WorldCover** land-cover classification (GeoTIFF).

Both are *static reference datasets*.  A single WorldCover snapshot and a
digital elevation model cannot, on their own, establish an environmental trend
over time.  This module therefore only provides geographic context (elevation,
terrain, land-cover description) and never reports a trend from these files.

Large rasters are read window-by-window with ``rasterio`` so a full
high-resolution grid is never loaded into memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Official ESA WorldCover 2021 class codes.
WORLDCOVER_CLASSES: dict[int, str] = {
    0: "No data",
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen",
}


@dataclass
class RasterInfo:
    available: bool
    path: str | None = None
    product: str | None = None
    crs: str | None = None
    bounds: list[float] | None = None
    resolution: list[float] | None = None
    nodata: float | None = None
    dtype: str | None = None
    width: int | None = None
    height: int | None = None
    note: str = ""
    error: str | None = None


@dataclass
class GeospatialContext:
    latitude: float
    longitude: float
    elevation_m: float | None = None
    land_cover_code: int | None = None
    land_cover_class: str | None = None
    nasadem: RasterInfo | None = None
    worldcover: RasterInfo | None = None
    notes: list[str] = field(default_factory=list)


def _rasterio():
    try:
        import rasterio  # noqa: F401
        from rasterio.windows import from_bounds  # noqa: F401

        return rasterio
    except ImportError:  # pragma: no cover - optional dependency
        return None


def inspect_raster(path: Path, product: str) -> RasterInfo:
    rasterio = _rasterio()
    if rasterio is None:
        return RasterInfo(
            available=False,
            product=product,
            path=str(path),
            note="rasterio is not installed; geospatial context disabled.",
        )
    if not path.exists():
        return RasterInfo(available=False, product=product, path=str(path), note="File not found.")

    try:
        with rasterio.open(path) as dataset:
            return RasterInfo(
                available=True,
                path=str(path),
                product=product,
                crs=str(dataset.crs) if dataset.crs else None,
                bounds=list(dataset.bounds),
                resolution=list(dataset.res),
                nodata=dataset.nodata,
                dtype=dataset.dtypes[0] if dataset.dtypes else None,
                width=dataset.width,
                height=dataset.height,
                note="Static reference dataset (no temporal dimension).",
            )
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to inspect %s: %s", path, exc)
        return RasterInfo(available=False, product=product, path=str(path), error=str(exc))


def _sample_point(path: Path, latitude: float, longitude: float) -> float | None:
    rasterio = _rasterio()
    if rasterio is None:
        return None
    try:
        from rasterio.warp import transform

        with rasterio.open(path) as dataset:
            xs, ys = transform("EPSG:4326", dataset.crs, [longitude], [latitude])
            row, col = dataset.index(xs[0], ys[0])
            if row < 0 or col < 0 or row >= dataset.height or col >= dataset.width:
                return None
            # Read a single pixel window.
            from rasterio.windows import Window

            window = Window(col, row, 1, 1)
            data = dataset.read(1, window=window)
            value = float(data[0, 0])
            if dataset.nodata is not None and abs(value - dataset.nodata) < 1e-6:
                return None
            return value
    except Exception as exc:  # pragma: no cover - defensive
        logger.info("Point sampling failed for %s: %s", path, exc)
        return None


def get_context(latitude: float, longitude: float) -> GeospatialContext:
    """Return available static geographic context for a coordinate."""
    context = GeospatialContext(latitude=latitude, longitude=longitude)

    if not settings.geospatial_enabled:
        context.notes.append("Geospatial context module is disabled by configuration.")
        return context

    if settings.nasadem_path:
        info = inspect_raster(Path(settings.nasadem_path), "NASADEM")
        context.nasadem = info
        if info.available:
            context.elevation_m = _sample_point(Path(settings.nasadem_path), latitude, longitude)
            context.notes.append("Elevation is a static terrain reference value, not a time series.")

    if settings.worldcover_path:
        info = inspect_raster(Path(settings.worldcover_path), "ESA WorldCover")
        context.worldcover = info
        if info.available:
            code = _sample_point(Path(settings.worldcover_path), latitude, longitude)
            if code is not None:
                code_int = int(round(code))
                context.land_cover_code = code_int
                context.land_cover_class = WORLDCOVER_CLASSES.get(code_int, f"Unknown class {code_int}")
            context.notes.append(
                "Land cover is a single static snapshot and cannot establish a temporal trend."
            )

    if context.nasadem is None and context.worldcover is None:
        context.notes.append(
            "No local NASADEM or ESA WorldCover rasters are configured. Set NASADEM_PATH and "
            "WORLDCOVER_PATH to enable geographic context."
        )

    return context
