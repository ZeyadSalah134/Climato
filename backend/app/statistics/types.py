"""Shared statistical types and helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np

from app.core.timeutils import elapsed_years


@dataclass
class Series:
    """A validated, chronologically sorted observation series."""

    variable: str
    units: str
    dates: list[date]
    values: np.ndarray
    frequency: str = "monthly"
    labels: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        order = np.argsort([d.toordinal() for d in self.dates])
        self.dates = [self.dates[i] for i in order]
        self.values = np.asarray(self.values, dtype=float)[order]
        if self.labels:
            self.labels = [self.labels[i] for i in order]

    @property
    def n(self) -> int:
        return len(self.dates)

    @property
    def reference_date(self) -> date:
        return self.dates[0]

    def elapsed_years(self) -> np.ndarray:
        ref = self.reference_date
        return np.array([elapsed_years(ref, d) for d in self.dates], dtype=float)

    def with_values(self, values: np.ndarray) -> "Series":
        return Series(
            variable=self.variable,
            units=self.units,
            dates=list(self.dates),
            values=np.asarray(values, dtype=float),
            frequency=self.frequency,
            labels=list(self.labels),
        )


def units_per_year_label(units: str) -> str:
    return f"{units}/year" if units else "units/year"


def units_per_decade_label(units: str) -> str:
    return f"{units}/decade" if units else "units/decade"
