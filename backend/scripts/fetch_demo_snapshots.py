"""Fetch real NASA POWER snapshots for offline demonstration mode.

This script performs genuine NASA POWER requests and stores the responses as
JSON snapshots under ``data/samples``.  Each snapshot records its retrieval
date, source endpoint, dataset, location and period so the data can never be
mistaken for a live query or a fabricated series.

Usage::

    py backend/scripts/fetch_demo_snapshots.py

Run it only when you have network access.  The committed snapshots were
produced with this exact script.
"""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = REPO_ROOT / "data" / "samples"

BASE_URL = "https://power.larc.nasa.gov/api/temporal"
COMMUNITY = "SB"

# (variable code, display name, units)
VARIABLES = [
    ("T2M", "Air Temperature", "degC"),
    ("PRECTOTCORR", "Precipitation", "mm/day"),
    ("RH2M", "Relative Humidity", "%"),
    ("WS10M", "Wind Speed", "m/s"),
    ("ALLSKY_SFC_SW_DWN", "Solar Radiation", "MJ/m^2/day"),
]

# (id, name, latitude, longitude)
LOCATIONS = [
    ("cairo", "Cairo, Egypt", 30.0444, 31.2357),
    ("manaus", "Manaus, Amazonas, Brazil", -3.1190, -60.0217),
    ("nairobi", "Nairobi, Kenya", -1.2921, 36.8219),
]

MONTHLY_START = 1991
MONTHLY_END = 2024


def fetch(endpoint: str, params: dict[str, str]) -> dict:
    url = f"{BASE_URL}/{endpoint}/point"
    with httpx.Client(timeout=60.0) as client:
        response = client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def month_end(year: int, month: int) -> str:
    if month == 12:
        return date(year, 12, 31).isoformat()
    first_next = date(year + (1 if month == 12 else 0), (month % 12) + 1, 1)
    return date.fromordinal(first_next.toordinal() - 1).isoformat()


def build_snapshot(payload: dict, code: str, location, frequency: str) -> dict:
    header = payload.get("header", {})
    parameters = payload.get("parameters", {})
    block = payload["properties"]["parameter"][code]
    meta = parameters.get(code, {})

    observations = []
    for key, value in sorted(block.items()):
        if frequency == "monthly" and key.endswith("13"):
            continue
        if value is None or abs(float(value) + 999.0) < 1e-9:
            continue
        if frequency == "monthly":
            observations.append([month_end(int(key[:4]), int(key[4:6])), float(value)])
        else:
            observations.append(
                [f"{key[:4]}-{key[4:6]}-{key[6:8]}", float(value)]
            )

    _, name, lat, lon = location
    return {
        "id": f"{location[0]}_{code.lower()}_{frequency}",
        "variable": code,
        "variable_name": dict((v[0], v[1]) for v in VARIABLES).get(code, code),
        "units": meta.get("units", ""),
        "longname": meta.get("longname", ""),
        "frequency": frequency,
        "location": {"latitude": lat, "longitude": lon, "name": name},
        "coverage": {
            "start": observations[0][0] if observations else "",
            "end": observations[-1][0] if observations else "",
        },
        "provider": "NASA POWER",
        "dataset": "NASA POWER / MERRA-2 meteorological reanalysis",
        "source_url": "https://power.larc.nasa.gov/docs/services/api/temporal/",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
        "retrieval_endpoint": f"{BASE_URL}/{frequency}/point",
        "retrieval_params": {
            "community": COMMUNITY,
            "latitude": lat,
            "longitude": lon,
            "start": header.get("start", ""),
            "end": header.get("end", ""),
        },
        "api_version": (header.get("api") or {}).get("version", ""),
        "synthetic": False,
        "observations": observations,
    }


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    written = 0
    for location in LOCATIONS:
        _, name, lat, lon = location
        for code, _, _ in VARIABLES:
            params = {
                "parameters": code,
                "community": COMMUNITY,
                "longitude": f"{lon:.4f}",
                "latitude": f"{lat:.4f}",
                "start": str(MONTHLY_START),
                "end": str(MONTHLY_END),
                "format": "JSON",
            }
            print(f"Fetching monthly {code} for {name} ...", flush=True)
            try:
                payload = fetch("monthly", params)
            except httpx.HTTPError as exc:
                print(f"  ! failed: {exc}", file=sys.stderr)
                continue
            snapshot = build_snapshot(payload, code, location, "monthly")
            path = OUTPUT_DIR / f"{snapshot['id']}.json"
            path.write_text(json.dumps(snapshot), encoding="utf-8")
            written += 1
            print(f"  -> {path.name} ({len(snapshot['observations'])} points)")

    # One daily snapshot so the daily frequency path can be demonstrated offline.
    print("Fetching daily T2M for Cairo (2023) ...", flush=True)
    daily_params = {
        "parameters": "T2M",
        "community": COMMUNITY,
        "longitude": "31.2357",
        "latitude": "30.0444",
        "start": "20230101",
        "end": "20231231",
        "format": "JSON",
    }
    try:
        payload = fetch("daily", daily_params)
        snapshot = build_snapshot(payload, "T2M", LOCATIONS[0], "daily")
        path = OUTPUT_DIR / f"{snapshot['id']}.json"
        path.write_text(json.dumps(snapshot), encoding="utf-8")
        written += 1
        print(f"  -> {path.name} ({len(snapshot['observations'])} points)")
    except httpx.HTTPError as exc:
        print(f"  ! failed: {exc}", file=sys.stderr)

    print(f"\nWrote {written} snapshot(s) to {OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
