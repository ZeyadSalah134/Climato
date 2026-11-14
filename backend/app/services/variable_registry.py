"""The EarthTrend environmental variable registry.

This registry is the single source of truth for which environmental variables
the platform can analyse, what their physical units are, and where the data
comes from.  It intentionally separates *available* variables (verified
through the NASA POWER integration) from *planned* integrations so the API can
never present an unimplemented product as usable.
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from app.core.errors import UnsupportedVariableError
from app.schemas.variables import VariableInfo


@dataclass(frozen=True)
class VariableDefinition:
    id: str
    code: str
    scientific_name: str
    display_name: str
    description: str
    units: str
    category: str
    provider: str
    dataset: str
    product_type: str
    temporal_coverage: str
    spatial_coverage: str
    spatial_resolution: str
    frequencies: list[str]
    source_documentation: str
    limitations: list[str]
    status: str = "available"
    supported_by: str = "NASA_POWER"
    color: str = "#21C77A"
    keywords: list[str] = field(default_factory=list)

    def to_schema(self, sample_value: float | None = None) -> VariableInfo:
        data: dict[str, Any] = asdict(self)
        data.pop("keywords", None)
        return VariableInfo(**data, sample_value=sample_value)


POWER_LIMITATIONS = [
    "Values are provided on a regular grid cell and do not represent a "
    "point measurement at the exact requested coordinate.",
    "Meteorological parameters are derived from the MERRA-2 reanalysis and "
    "bias-corrected using satellite and ground observations; they are model "
    "estimates rather than direct in-situ measurements.",
    "Cells with sparse observational constraint (for example over open ocean "
    "or high latitudes) carry higher uncertainty.",
]

_POWER_DOC = "https://power.larc.nasa.gov/docs/services/api/temporal/"

POWER_VARIABLES: list[VariableDefinition] = [
    VariableDefinition(
        id="T2M",
        code="T2M",
        scientific_name="Near-surface air temperature at 2 m",
        display_name="Air Temperature",
        description=(
            "Temperature of the air at 2 metres above the surface. A primary "
            "indicator of regional warming and cooling."
        ),
        units="degC",
        category="Temperature",
        provider="NASA POWER (NASA Langley Research Center)",
        dataset="NASA POWER / MERRA-2 meteorological reanalysis",
        product_type="reanalysis",
        temporal_coverage="1981-01-01 to present (monthly and daily)",
        spatial_coverage="Global land and ocean",
        spatial_resolution="~0.5 deg x 0.625 deg (MERRA-2 grid)",
        frequencies=["monthly", "daily"],
        source_documentation=_POWER_DOC,
        limitations=POWER_LIMITATIONS,
        color="#F6B85E",
        keywords=["temperature", "warming", "heat", "warmer", "cooler", "thermal", "climate"],
    ),
    VariableDefinition(
        id="PRECTOTCORR",
        code="PRECTOTCORR",
        scientific_name="Bias-corrected total precipitation",
        display_name="Precipitation",
        description=(
            "Total precipitation (rain and snow water equivalent) corrected "
            "for known biases. Used to detect drying and wetting trends."
        ),
        units="mm/day",
        category="Water",
        provider="NASA POWER (NASA Langley Research Center)",
        dataset="NASA POWER / MERRA-2 precipitation with GPCP/ground bias correction",
        product_type="reanalysis",
        temporal_coverage="1981-01-01 to present (monthly and daily)",
        spatial_coverage="Global land and ocean",
        spatial_resolution="~0.5 deg x 0.625 deg (MERRA-2 grid)",
        frequencies=["monthly", "daily"],
        source_documentation=_POWER_DOC,
        limitations=POWER_LIMITATIONS
        + ["Precipitation is highly intermittent; monthly totals are far more "
           "stable than daily values."],
        color="#4FA8F5",
        keywords=["rain", "rainfall", "precipitation", "wet", "dry", "drought", "rainy", "water"],
    ),
    VariableDefinition(
        id="RH2M",
        code="RH2M",
        scientific_name="Relative humidity at 2 m",
        display_name="Relative Humidity",
        description=(
            "Ratio of actual to saturation water vapour at 2 metres, expressed "
            "as a percentage. Indicates atmospheric moisture and aridity."
        ),
        units="%",
        category="Water",
        provider="NASA POWER (NASA Langley Research Center)",
        dataset="NASA POWER / MERRA-2 meteorological reanalysis",
        product_type="reanalysis",
        temporal_coverage="1981-01-01 to present (monthly and daily)",
        spatial_coverage="Global land and ocean",
        spatial_resolution="~0.5 deg x 0.625 deg (MERRA-2 grid)",
        frequencies=["monthly", "daily"],
        source_documentation=_POWER_DOC,
        limitations=POWER_LIMITATIONS,
        color="#8EF0BB",
        keywords=["humidity", "moisture", "humid", "dry", "arid", "drier", "water vapour"],
    ),
    VariableDefinition(
        id="WS10M",
        code="WS10M",
        scientific_name="Wind speed at 10 m",
        display_name="Wind Speed",
        description=(
            "Magnitude of the horizontal wind vector at 10 metres above the "
            "surface. Relevant for renewable energy and atmospheric transport."
        ),
        units="m/s",
        category="Atmosphere",
        provider="NASA POWER (NASA Langley Research Center)",
        dataset="NASA POWER / MERRA-2 meteorological reanalysis",
        product_type="reanalysis",
        temporal_coverage="1981-01-01 to present (monthly and daily)",
        spatial_coverage="Global land and ocean",
        spatial_resolution="~0.5 deg x 0.625 deg (MERRA-2 grid)",
        frequencies=["monthly", "daily"],
        source_documentation=_POWER_DOC,
        limitations=POWER_LIMITATIONS,
        color="#A78BFA",
        keywords=["wind", "windy", "gust", "breeze", "energy", "circulation"],
    ),
    VariableDefinition(
        id="ALLSKY_SFC_SW_DWN",
        code="ALLSKY_SFC_SW_DWN",
        scientific_name="All-sky surface shortwave downward irradiance",
        display_name="Solar Radiation",
        description=(
            "Downward solar irradiance reaching the surface under all sky "
            "conditions, including cloud cover. Drives surface energy balance "
            "and photovoltaic yield."
        ),
        units="MJ/m^2/day",
        category="Energy",
        provider="NASA POWER (NASA Langley Research Center)",
        dataset="NASA POWER / CERES synoptic + MERRA-2 meteorology",
        product_type="satellite_observation",
        temporal_coverage="1984-01-01 to present (monthly and daily)",
        spatial_coverage="Global land and ocean",
        spatial_resolution="~1 deg x 1 deg (CERES synoptic grid)",
        frequencies=["monthly", "daily"],
        source_documentation=_POWER_DOC,
        limitations=POWER_LIMITATIONS
        + ["Derived from satellite cloud observations combined with a "
           "radiative transfer model, so it is not a direct surface measurement."],
        color="#F6E05E",
        keywords=["solar", "radiation", "sunshine", "irradiance", "energy", "cloud", "brightness"],
    ),
]

# --------------------------------------------------------------------------
# Planned integrations.  These are documented and designed for, but the
# adapter is not yet wired to a verified, working access method.  They are
# surfaced through the API explicitly labelled ``planned_integration`` so the
# platform never presents them as available.
# --------------------------------------------------------------------------
PLANNED_VARIABLES: list[VariableDefinition] = [
    VariableDefinition(
        id="GPM_IMERG_PRECIP",
        code="GPM_3IMERGM",
        scientific_name="GPM IMERG monthly precipitation",
        display_name="GPM Precipitation (planned)",
        description="Satellite-based global precipitation from the GPM IMERG product.",
        units="mm/month",
        category="Water",
        provider="NASA GES DISC",
        dataset="GPM IMERG Monthly (GPM_3IMERGM v07)",
        product_type="satellite_observation",
        temporal_coverage="2000-06 to present",
        spatial_coverage="Global 60N-60S",
        spatial_resolution="0.1 deg",
        frequencies=["monthly"],
        source_documentation="https://disc.gsfc.nasa.gov/datasets/GPM_3IMERGM_07/summary",
        limitations=["Requires NASA Earthdata authentication for automated retrieval."],
        status="planned_integration",
        supported_by="GES_DISC",
        color="#4FA8F5",
    ),
    VariableDefinition(
        id="MODIS_NDVI",
        code="MOD13A3",
        scientific_name="MODIS monthly NDVI",
        display_name="Vegetation Index (planned)",
        description="Normalised Difference Vegetation Index describing vegetation greenness.",
        units="index",
        category="Land",
        provider="NASA LP DAAC",
        dataset="MODIS/Terra Vegetation Indices Monthly L3 Global 1 km (MOD13A3)",
        product_type="satellite_observation",
        temporal_coverage="2000-02 to present",
        spatial_coverage="Global land",
        spatial_resolution="1 km",
        frequencies=["monthly"],
        source_documentation="https://lpdaac.usgs.gov/products/mod13a3v061/",
        limitations=["Requires NASA Earthdata authentication and large raster handling."],
        status="planned_integration",
        supported_by="LP_DAAC",
        color="#21C77A",
    ),
    VariableDefinition(
        id="MERRA2_AOD",
        code="TOTEXTTAU",
        scientific_name="MERRA-2 total aerosol optical depth",
        display_name="Aerosol Optical Depth (planned)",
        description="Column-integrated aerosol optical depth from the MERRA-2 reanalysis.",
        units="dimensionless",
        category="Atmosphere",
        provider="NASA GES DISC",
        dataset="MERRA-2 (M2T1NXAER)",
        product_type="reanalysis",
        temporal_coverage="1980-01 to present",
        spatial_coverage="Global",
        spatial_resolution="0.5 deg x 0.625 deg",
        frequencies=["hourly", "monthly"],
        source_documentation="https://disc.gsfc.nasa.gov/datasets/M2T1NXAER_5.12.4/summary",
        limitations=["Requires Earthdata authentication and NetCDF subsetting."],
        status="planned_integration",
        supported_by="GES_DISC",
        color="#F6B85E",
    ),
    VariableDefinition(
        id="GLDAS_SOIL_MOISTURE",
        code="GLDAS_NOAH025_M",
        scientific_name="GLDAS surface soil moisture",
        display_name="Soil Moisture (planned)",
        description="Modeled surface soil moisture from the GLDAS land-surface model.",
        units="kg/m^2",
        category="Land",
        provider="NASA GES DISC",
        dataset="GLDAS Noah 2.1 (GLDAS_NOAH025_M)",
        product_type="model_estimate",
        temporal_coverage="2000-01 to present",
        spatial_coverage="Global land",
        spatial_resolution="0.25 deg",
        frequencies=["monthly"],
        source_documentation="https://disc.gsfc.nasa.gov/datasets/GLDAS_NOAH025_M_2.1/summary",
        limitations=["Land-surface model output, not a direct observation."],
        status="planned_integration",
        supported_by="GES_DISC",
        color="#8EF0BB",
    ),
    VariableDefinition(
        id="AIRS_TEMP",
        code="AIRS3STM",
        scientific_name="AIRS level-3 surface air temperature",
        display_name="AIRS Temperature (planned)",
        description="Atmospheric temperature profile retrievals from the AIRS instrument.",
        units="K",
        category="Temperature",
        provider="NASA GES DISC",
        dataset="AIRS Level 3 Standard Monthly (AIRS3STM)",
        product_type="satellite_observation",
        temporal_coverage="2002-09 to present",
        spatial_coverage="Global",
        spatial_resolution="1 deg",
        frequencies=["monthly"],
        source_documentation="https://disc.gsfc.nasa.gov/datasets/AIRS3STM_7.0/summary",
        limitations=["Requires Earthdata authentication."],
        status="planned_integration",
        supported_by="GES_DISC",
        color="#F6B85E",
    ),
    VariableDefinition(
        id="OMI_NO2",
        code="OMNO2d",
        scientific_name="OMI tropospheric NO2 column",
        display_name="Nitrogen Dioxide (planned)",
        description="Tropospheric nitrogen dioxide column density from the OMI instrument.",
        units="molecules/cm^2",
        category="Atmosphere",
        provider="NASA GES DISC",
        dataset="OMI/Aura NO2 Tropospheric Column (OMNO2d)",
        product_type="satellite_observation",
        temporal_coverage="2004-10 to present",
        spatial_coverage="Global",
        spatial_resolution="0.25 deg",
        frequencies=["daily", "monthly"],
        source_documentation="https://disc.gsfc.nasa.gov/datasets/OMNO2d_003/summary",
        limitations=["Requires Earthdata authentication; air-quality applications "
                     "should account for cloud screening."],
        status="planned_integration",
        supported_by="GES_DISC",
        color="#A78BFA",
    ),
]

ALL_VARIABLES: list[VariableDefinition] = POWER_VARIABLES + PLANNED_VARIABLES
_BY_ID = {v.id: v for v in ALL_VARIABLES}
_AVAILABLE = {v.id: v for v in POWER_VARIABLES}


def list_variables(include_planned: bool = True) -> list[VariableDefinition]:
    return ALL_VARIABLES if include_planned else list(POWER_VARIABLES)


def get_variable(variable_id: str, *, require_available: bool = False) -> VariableDefinition:
    key = variable_id.strip()
    definition = _BY_ID.get(key)
    if definition is None:
        raise UnsupportedVariableError(
            f"Unknown environmental variable '{variable_id}'.",
            details={"available_variables": list(_AVAILABLE)},
        )
    if require_available and definition.status != "available":
        raise UnsupportedVariableError(
            f"Variable '{variable_id}' is a planned integration and cannot be analysed yet.",
            details={"status": definition.status, "available_variables": list(_AVAILABLE)},
        )
    return definition


def available_variable_ids() -> list[str]:
    return list(_AVAILABLE)


def variables_by_category() -> dict[str, list[VariableDefinition]]:
    grouped: dict[str, list[VariableDefinition]] = {}
    for variable in ALL_VARIABLES:
        grouped.setdefault(variable.category, []).append(variable)
    return grouped
