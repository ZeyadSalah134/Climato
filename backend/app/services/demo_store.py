"""Offline demonstration dataset store.

Demonstration data consists of **real, previously retrieved NASA POWER
responses** stored as JSON snapshots under ``data/samples``.  Each snapshot
records its retrieval date, source endpoint, dataset, location and period so it
can never be mistaken for a live query or a fabricated series.

The store is only used as an explicit fallback when live retrieval fails and
``ALLOW_DEMO_FALLBACK`` is enabled, or when a caller opts in.  Results are
always marked ``retrieval_mode="demo"`` and carry a provenance warning.
"""

from __future__ import annotations

import json
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

# Maximum great-circle-ish tolerance (degrees) between a request and a snapshot
# location for the snapshot to be considered representative.
LOCATION_TOLERANCE_DEG = 1.5


@dataclass
class DemoSample:
    id: str
    variable: str
    variable_name: str
    units: str
    frequency: str
    latitude: float
    longitude: float
    location_name: str
    coverage_start: date
    coverage_end: date
    provider: str
    dataset: str
    source_url: str
    retrieved_at: str
    retrieval_endpoint: str
    observations: list[tuple[date, float]]
    longname: str = ""
    api_version: str = ""
    synthetic: bool = False

    def to_public(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "variable": self.variable,
            "variable_name": self.variable_name,
            "units": self.units,
            "frequency": self.frequency,
            "location": {
                "latitude": self.latitude,
                "longitude": self.longitude,
                "name": self.location_name,
            },
            "coverage": {"start": self.coverage_start.isoformat(), "end": self.coverage_end.isoformat()},
            "provider": self.provider,
            "dataset": self.dataset,
            "source_url": self.source_url,
            "retrieved_at": self.retrieved_at,
            "retrieval_endpoint": self.retrieval_endpoint,
            "n_observations": len(self.observations),
            "synthetic": self.synthetic,
        }


def _load_file(path: Path) -> DemoSample | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Skipping unreadable demo snapshot %s: %s", path, exc)
        return None
    try:
        coverage = raw.get("coverage", {})
        observations = [
            (parse_iso_date(item[0]), float(item[1]))
            for item in raw.get("observations", [])
            if item and item[1] is not None
        ]
        return DemoSample(
            id=raw["id"],
            variable=raw["variable"],
            variable_name=raw.get("variable_name", raw["variable"]),
            units=raw.get("units", ""),
            frequency=raw.get("frequency", "monthly"),
            latitude=float(raw["location"]["latitude"]),
            longitude=float(raw["location"]["longitude"]),
            location_name=raw["location"].get("name", ""),
            coverage_start=parse_iso_date(coverage["start"]),
            coverage_end=parse_iso_date(coverage["end"]),
            provider=raw.get("provider", "NASA POWER"),
            dataset=raw.get("dataset", ""),
            source_url=raw.get("source_url", ""),
            retrieved_at=str(raw.get("retrieved_at", "")),
            retrieval_endpoint=raw.get("retrieval_endpoint", ""),
            observations=observations,
            longname=raw.get("longname", ""),
            api_version=raw.get("api_version", ""),
            synthetic=bool(raw.get("synthetic", False)),
        )
    except (KeyError, TypeError, ValueError) as exc:
        logger.warning("Malformed demo snapshot %s: %s", path, exc)
        return None


@lru_cache
def _samples() -> tuple[DemoSample, ...]:
    directory = settings.demo_data_dir
    if not directory.exists():
        return ()
    samples: list[DemoSample] = []
    for path in sorted(directory.glob("*.json")):
        sample = _load_file(path)
        if sample is not None:
            samples.append(sample)
    logger.info("Loaded %s demonstration snapshot(s) from %s", len(samples), directory)
    return tuple(samples)


def list_samples() -> list[DemoSample]:
    return list(_samples())


def reload_samples() -> None:
    _samples.cache_clear()


def find_sample(
    *,
    variable: str,
    frequency: str,
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
) -> DemoSample | None:
    """Return the closest matching snapshot, or ``None``.

    A snapshot matches only when the variable and frequency agree, the
    requested period overlaps the snapshot coverage, and the requested
    coordinate lies within :data:`LOCATION_TOLERANCE_DEG` degrees of the
    snapshot location.
    """
    best: DemoSample | None = None
    best_distance = float("inf")
    for sample in _samples():
        if sample.variable != variable or sample.frequency != frequency:
            continue
        if end_date < sample.coverage_start or start_date > sample.coverage_end:
            continue
        distance = max(abs(sample.latitude - latitude), abs(sample.longitude - longitude))
        if distance <= LOCATION_TOLERANCE_DEG and distance < best_distance:
            best, best_distance = sample, distance
    return best


def sample_to_series(
    sample: DemoSample,
    *,
    start_date: date,
    end_date: date,
) -> ProviderSeries:
    observations = [(d, v) for d, v in sample.observations if start_date <= d <= end_date]
    note = (
        "Demonstration snapshot: this series is real previously-retrieved NASA "
        f"POWER data for {sample.location_name} ({sample.latitude:.4f}, "
        f"{sample.longitude:.4f}), retrieved {sample.retrieved_at}. It is not a "
        "live query for the requested coordinate."
    )
    if sample.synthetic:
        note = (
            "SYNTHETIC TEST FIXTURE: this series is generated for testing and "
            "must not be interpreted as an Earth observation."
        )
    return ProviderSeries(
        variable_code=sample.variable,
        units=sample.units,
        longname=sample.longname or sample.variable_name,
        observations=observations,
        missing=[],
        fill_value=-999.0,
        request_url=sample.retrieval_endpoint,
        request_params={"snapshot_id": sample.id},
        source_name=sample.provider,
        api_version=sample.api_version,
        retrieval_mode="demo",
        notes=[note],
    )
