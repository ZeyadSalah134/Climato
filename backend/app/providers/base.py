"""Provider abstraction for Earth observation data sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Protocol


@dataclass
class ProviderSeries:
    """Normalised output produced by every data provider adapter."""

    variable_code: str
    units: str
    longname: str
    observations: list[tuple[date, float]] = field(default_factory=list)
    missing: list[date] = field(default_factory=list)
    fill_value: float | None = None
    request_url: str = ""
    request_params: dict = field(default_factory=dict)
    source_name: str = ""
    api_version: str = ""
    retrieval_mode: str = "live"
    notes: list[str] = field(default_factory=list)


class DataProvider(Protocol):
    """Structural type for a time-series data provider."""

    name: str

    async def fetch_series(
        self,
        *,
        variable_code: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        frequency: str,
    ) -> ProviderSeries:  # pragma: no cover - protocol definition
        ...
