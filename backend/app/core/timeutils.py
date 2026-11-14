"""Small reusable time helpers for scientific time series."""

from __future__ import annotations

from datetime import date, datetime

# Julian year length. Using a fixed constant keeps "per year" rates
# reproducible and interpretable for both daily and monthly sampling.
DAYS_PER_YEAR = 365.25


def parse_iso_date(value: str | date | datetime) -> date:
    """Parse an ISO date string (``YYYY-MM-DD``) or passthrough a date."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d", "%Y-%m"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unrecognised date format: {value!r}")


def elapsed_years(reference: date, moment: date) -> float:
    """Elapsed time in years between two dates using actual day counts."""
    return (moment - reference).days / DAYS_PER_YEAR


def month_end(year: int, month: int) -> date:
    """Return the last calendar day of a month (handles leap years)."""
    if month == 12:
        return date(year, 12, 31)
    first_of_next = date(year + (1 if month == 12 else 0), (month % 12) + 1, 1)
    return date.fromordinal(first_of_next.toordinal() - 1)
