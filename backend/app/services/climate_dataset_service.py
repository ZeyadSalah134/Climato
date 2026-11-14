"""Service for querying and serving the verified NASA POWER climate dataset.

Loads and indexes ``climate_power_monthly_2000-2025.csv`` containing 28,080 verified
monthly NASA POWER climate observations (2000-2025) across 30 grid points in Egypt
(Cairo, Alexandria, Nile Delta, Canal zone, Beni Suef).

Provides:
1. Direct matching of queries to verified observations.
2. Geographical metadata and named regional stations.
3. Provenance and metadata linking to the verified deliverable dataset.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger
from app.core.timeutils import parse_iso_date
from app.providers.base import ProviderSeries

logger = get_logger(__name__)

# Search paths for the verified dataset
DATASET_PATHS = [
    Path(settings.cache_dir).parent / "climate_power_monthly_2000-2025.csv",
    Path(__file__).resolve().parents[3] / "climate_power_monthly_2000-2025.csv",
    Path(__file__).resolve().parents[3] / "data" / "climate_power_monthly_2000-2025.csv",
]

# Regional station labels for the 30 grid points in Egypt
GRID_POINT_NAMES: dict[str, str] = {
    "30.0_31.25": "Cairo Central / Giza, Egypt",
    "30.0_31.875": "Cairo East / New Cairo, Egypt",
    "30.0_30.625": "Giza West / 6th of October, Egypt",
    "30.0_30.0": "Western Desert East / Wadi El Farigh",
    "30.0_29.375": "Western Desert / Qattara Rim South",
    "30.0_32.5": "Suez & Southern Suez Canal, Egypt",
    "30.5_31.25": "Southern Nile Delta / Benha - Qalyubia",
    "30.5_31.875": "Sharkia / Zagazig, Egypt",
    "30.5_30.625": "Menoufia / Sadat City, Egypt",
    "30.5_30.0": "Wadi El Natrun, Beheira, Egypt",
    "30.5_29.375": "Western Desert Interior North",
    "30.5_32.5": "Ismailia & Central Suez Canal, Egypt",
    "31.0_31.25": "Central Nile Delta / Tanta - Gharbia",
    "31.0_31.875": "Eastern Nile Delta / Mansoura - Dakahlia",
    "31.0_30.625": "Kafr El Sheikh South / Damanhour East",
    "31.0_30.0": "Alexandria South / Beheira / Damanhour",
    "31.0_29.375": "El Alamein South / Coastal Plateau",
    "31.0_32.5": "Port Said South / Northern Suez Canal",
    "31.5_31.25": "Northern Nile Delta Coast / Baltim",
    "31.5_31.875": "Damietta & Nile Delta Estuary",
    "31.5_30.625": "Kafr El Sheikh Coast / Lake Burullus",
    "31.5_30.0": "Alexandria Coastal Metro / Abu Qir",
    "31.5_29.375": "North Coast / El Alamein, Egypt",
    "31.5_32.5": "Port Said Coastal & Mediterranean Gate",
    "29.5_31.25": "Beni Suef & Middle Nile Valley",
    "29.5_31.875": "Eastern Desert North / Zaafarana Plateau",
    "29.5_30.625": "Fayoum Oasis & Lake Qarun, Egypt",
    "29.5_30.0": "Western Desert / Wadi El Rayan West",
    "29.5_29.375": "Western Desert / Bahariya Rim North",
    "29.5_32.5": "Gulf of Suez / Ain Sokhna Coast",
}

VARIABLE_INFO: dict[str, dict[str, str]] = {
    "T2M": {
        "name": "Air Temperature",
        "units": "degC",
        "longname": "Near-surface air temperature at 2 m",
    },
    "PRECTOTCORR": {
        "name": "Precipitation",
        "units": "mm/day",
        "longname": "Bias-corrected total precipitation",
    },
    "ALLSKY_SFC_SW_DWN": {
        "name": "Solar Radiation",
        "units": "MJ/m^2/day",
        "longname": "All-sky surface shortwave downward irradiance",
    },
}


@dataclass(frozen=True)
class GridStation:
    point_id: str
    latitude: float
    longitude: float
    name: str


@lru_cache(maxsize=1)
def get_dataset_csv_path() -> Path | None:
    for p in DATASET_PATHS:
        if p.exists() and p.is_file():
            return p
    return None


@lru_cache(maxsize=1)
def load_verified_stations() -> list[GridStation]:
    path = get_dataset_csv_path()
    if not path:
        return []
    stations: dict[str, GridStation] = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row["point_id"]
                if pid not in stations:
                    lat = float(row["lat"])
                    lon = float(row["lon"])
                    name = GRID_POINT_NAMES.get(pid, f"Grid Cell {pid} (Egypt)")
                    stations[pid] = GridStation(point_id=pid, latitude=lat, longitude=lon, name=name)
    except Exception as exc:
        logger.warning("Error loading verified stations from %s: %s", path, exc)
    return sorted(stations.values(), key=lambda s: s.name)


class ClimateDatasetService:
    """Manages queries into the 2000-2025 verified NASA POWER climate dataset."""

    def __init__(self) -> None:
        self._data: dict[tuple[str, str], list[tuple[date, float, float]]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        path = get_dataset_csv_path()
        if not path:
            logger.warning("Verified climate dataset CSV not found.")
            self._loaded = True
            return

        logger.info("Loading verified climate dataset from %s ...", path)
        count = 0
        try:
            with open(path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    pid = row["point_id"]
                    var = row["variable"]
                    dt = parse_iso_date(row["date"])
                    val = float(row["value"])
                    anom = float(row.get("anomaly", 0.0))
                    key = (pid, var)
                    if key not in self._data:
                        self._data[key] = []
                    self._data[key].append((dt, val, anom))
                    count += 1
            for k in self._data:
                self._data[k].sort(key=lambda x: x[0])
            self._loaded = True
            logger.info("Loaded %d verified climate observations across %d series.", count, len(self._data))
        except Exception as exc:
            logger.error("Failed loading verified climate dataset: %s", exc)
            self._loaded = True

    def find_nearest_station(self, latitude: float, longitude: float, max_dist_deg: float = 0.5) -> GridStation | None:
        stations = load_verified_stations()
        best_station: GridStation | None = None
        best_dist = float("inf")
        for s in stations:
            # Manhattan / max-coord distance for regular grid
            dist = max(abs(s.latitude - latitude), abs(s.longitude - longitude))
            if dist <= max_dist_deg and dist < best_dist:
                best_dist = dist
                best_station = s
        return best_station

    def get_series(
        self,
        *,
        variable: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
    ) -> ProviderSeries | None:
        if variable not in VARIABLE_INFO:
            return None

        station = self.find_nearest_station(latitude, longitude, max_dist_deg=0.5)
        if not station:
            return None

        self._ensure_loaded()
        key = (station.point_id, variable)
        all_obs = self._data.get(key)
        if not all_obs:
            return None

        # Filter by requested date range
        filtered = [(d, v) for d, v, _ in all_obs if start_date <= d <= end_date]
        if not filtered:
            return None

        info = VARIABLE_INFO[variable]
        notes = [
            f"Climato Verified NASA POWER Dataset: real monthly observations for {station.name} "
            f"({station.latitude:.4f} N, {station.longitude:.4f} E) from 2000-01 to 2025-12.",
            "Source: NASA POWER (MERRA-2 reanalysis & satellite observations; agroclimatology monthly point data).",
        ]

        return ProviderSeries(
            variable_code=variable,
            units=info["units"],
            longname=info["longname"],
            observations=filtered,
            missing=[],
            fill_value=-999.0,
            request_url="local://climate_power_monthly_2000-2025.csv",
            request_params={"point_id": station.point_id, "variable": variable, "source": "Climato Repository Dataset"},
            source_name="NASA POWER (AG, monthly; Climato project dataset)",
            api_version="Climato-2026",
            retrieval_mode="verified_dataset",
            notes=notes,
        )


climate_dataset_service = ClimateDatasetService()
