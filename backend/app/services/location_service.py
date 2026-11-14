"""Location search service.

Uses the OpenStreetMap Nominatim geocoder when the network is available and
falls back to a curated offline gazetteer of major cities so the Earth
Explorer remains usable without internet access.  The offline gazetteer is a
small static reference dataset and is labelled as such in responses.
"""

from __future__ import annotations

from dataclasses import dataclass

import httpx

from app.core.logging import get_logger
from app.schemas.location import LocationResult, LocationSearchResponse

logger = get_logger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "EarthTrend/1.0 (NASA Space Apps Challenge project; educational use)"


@dataclass(frozen=True)
class GazetteerEntry:
    name: str
    display_name: str
    latitude: float
    longitude: float
    country: str
    region: str


# A small static reference gazetteer (not an Earth observation dataset).
OFFLINE_GAZETTEER: list[GazetteerEntry] = [
    GazetteerEntry("Cairo", "Cairo, Egypt", 30.0444, 31.2357, "Egypt", "Africa"),
    GazetteerEntry("Alexandria", "Alexandria, Egypt", 31.2001, 29.9187, "Egypt", "Africa"),
    GazetteerEntry("Aswan", "Aswan, Egypt", 24.0889, 32.8998, "Egypt", "Africa"),
    # --- 30 Verified NASA POWER Grid Stations across Egypt ---
    GazetteerEntry("Cairo Central", "Cairo Central / Giza, Egypt (NASA Station)", 30.0, 31.25, "Egypt", "Nile Valley"),
    GazetteerEntry("New Cairo", "Cairo East / New Cairo, Egypt (NASA Station)", 30.0, 31.875, "Egypt", "Cairo Metro"),
    GazetteerEntry("6th of October", "Giza West / 6th of October, Egypt (NASA Station)", 30.0, 30.625, "Egypt", "Giza"),
    GazetteerEntry("Suez", "Suez & Southern Suez Canal, Egypt (NASA Station)", 30.0, 32.5, "Egypt", "Canal Zone"),
    GazetteerEntry("Benha", "Southern Nile Delta / Benha - Qalyubia (NASA Station)", 30.5, 31.25, "Egypt", "Delta"),
    GazetteerEntry("Zagazig", "Sharkia / Zagazig, Egypt (NASA Station)", 30.5, 31.875, "Egypt", "Delta"),
    GazetteerEntry("Sadat City", "Menoufia / Sadat City, Egypt (NASA Station)", 30.5, 30.625, "Egypt", "Delta"),
    GazetteerEntry("Wadi El Natrun", "Wadi El Natrun, Beheira, Egypt (NASA Station)", 30.5, 30.0, "Egypt", "Western Delta"),
    GazetteerEntry("Ismailia", "Ismailia & Central Suez Canal, Egypt (NASA Station)", 30.5, 32.5, "Egypt", "Canal Zone"),
    GazetteerEntry("Tanta", "Central Nile Delta / Tanta - Gharbia (NASA Station)", 31.0, 31.25, "Egypt", "Delta"),
    GazetteerEntry("Mansoura", "Eastern Nile Delta / Mansoura - Dakahlia (NASA Station)", 31.0, 31.875, "Egypt", "Delta"),
    GazetteerEntry("Damanhour", "Kafr El Sheikh South / Damanhour East (NASA Station)", 31.0, 30.625, "Egypt", "Delta"),
    GazetteerEntry("Alexandria South", "Alexandria South / Beheira (NASA Station)", 31.0, 30.0, "Egypt", "Coastal"),
    GazetteerEntry("El Alamein South", "El Alamein South / Coastal Plateau (NASA Station)", 31.0, 29.375, "Egypt", "North Coast"),
    GazetteerEntry("Port Said South", "Port Said South / Northern Suez Canal (NASA Station)", 31.0, 32.5, "Egypt", "Canal Zone"),
    GazetteerEntry("Baltim", "Northern Nile Delta Coast / Baltim (NASA Station)", 31.5, 31.25, "Egypt", "Coast"),
    GazetteerEntry("Damietta", "Damietta & Nile Delta Estuary (NASA Station)", 31.5, 31.875, "Egypt", "Coast"),
    GazetteerEntry("Lake Burullus", "Kafr El Sheikh Coast / Lake Burullus (NASA Station)", 31.5, 30.625, "Egypt", "Coast"),
    GazetteerEntry("Alexandria Coast", "Alexandria Coastal Metro / Abu Qir (NASA Station)", 31.5, 30.0, "Egypt", "Coast"),
    GazetteerEntry("El Alamein", "North Coast / El Alamein, Egypt (NASA Station)", 31.5, 29.375, "Egypt", "North Coast"),
    GazetteerEntry("Port Said", "Port Said Coastal & Mediterranean Gate (NASA Station)", 31.5, 32.5, "Egypt", "Canal Zone"),
    GazetteerEntry("Beni Suef", "Beni Suef & Middle Nile Valley (NASA Station)", 29.5, 31.25, "Egypt", "Middle Egypt"),
    GazetteerEntry("Zaafarana", "Eastern Desert North / Zaafarana Plateau (NASA Station)", 29.5, 31.875, "Egypt", "Red Sea"),
    GazetteerEntry("Fayoum", "Fayoum Oasis & Lake Qarun, Egypt (NASA Station)", 29.5, 30.625, "Egypt", "Middle Egypt"),
    GazetteerEntry("Ain Sokhna", "Gulf of Suez / Ain Sokhna Coast (NASA Station)", 29.5, 32.5, "Egypt", "Red Sea"),
    GazetteerEntry("Aswan", "Aswan High Dam, Egypt (NASA Context)", 24.0889, 32.8998, "Egypt", "Upper Egypt"),
    # --- Global Reference Hubs ---
    GazetteerEntry("Nairobi", "Nairobi, Kenya", -1.2921, 36.8219, "Kenya", "Africa"),
    GazetteerEntry("Lagos", "Lagos, Nigeria", 6.5244, 3.3792, "Nigeria", "Africa"),
    GazetteerEntry("Cape Town", "Cape Town, South Africa", -33.9249, 18.4241, "South Africa", "Africa"),
    GazetteerEntry("Manaus", "Manaus, Amazonas, Brazil", -3.1190, -60.0217, "Brazil", "South America"),
    GazetteerEntry("Belem", "Belem, Para, Brazil", -1.4558, -48.4902, "Brazil", "South America"),
    GazetteerEntry("Sao Paulo", "Sao Paulo, Brazil", -23.5505, -46.6333, "Brazil", "South America"),
    GazetteerEntry("Buenos Aires", "Buenos Aires, Argentina", -34.6037, -58.3816, "Argentina", "South America"),
    GazetteerEntry("Lima", "Lima, Peru", -12.0464, -77.0428, "Peru", "South America"),
    GazetteerEntry("Bogota", "Bogota, Colombia", 4.7110, -74.0721, "Colombia", "South America"),
    GazetteerEntry("New York", "New York City, New York, USA", 40.7128, -74.0060, "United States", "North America"),
    GazetteerEntry("Los Angeles", "Los Angeles, California, USA", 34.0522, -118.2437, "United States", "North America"),
    GazetteerEntry("Phoenix", "Phoenix, Arizona, USA", 33.4484, -112.0740, "United States", "North America"),
    GazetteerEntry("Mexico City", "Mexico City, Mexico", 19.4326, -99.1332, "Mexico", "North America"),
    GazetteerEntry("Toronto", "Toronto, Ontario, Canada", 43.6532, -79.3832, "Canada", "North America"),
    GazetteerEntry("Anchorage", "Anchorage, Alaska, USA", 61.2181, -149.9003, "United States", "North America"),
    GazetteerEntry("London", "London, United Kingdom", 51.5074, -0.1278, "United Kingdom", "Europe"),
    GazetteerEntry("Paris", "Paris, France", 48.8566, 2.3522, "France", "Europe"),
    GazetteerEntry("Madrid", "Madrid, Spain", 40.4168, -3.7038, "Spain", "Europe"),
    GazetteerEntry("Berlin", "Berlin, Germany", 52.5200, 13.4050, "Germany", "Europe"),
    GazetteerEntry("Rome", "Rome, Italy", 41.9028, 12.4964, "Italy", "Europe"),
    GazetteerEntry("Moscow", "Moscow, Russia", 55.7558, 37.6173, "Russia", "Europe"),
    GazetteerEntry("Reykjavik", "Reykjavik, Iceland", 64.1466, -21.9426, "Iceland", "Europe"),
    GazetteerEntry("Istanbul", "Istanbul, Turkey", 41.0082, 28.9784, "Turkey", "Europe"),
    GazetteerEntry("Dubai", "Dubai, United Arab Emirates", 25.2048, 55.2708, "United Arab Emirates", "Asia"),
    GazetteerEntry("Riyadh", "Riyadh, Saudi Arabia", 24.7136, 46.6753, "Saudi Arabia", "Asia"),
    GazetteerEntry("Delhi", "Delhi, India", 28.6139, 77.2090, "India", "Asia"),
    GazetteerEntry("Mumbai", "Mumbai, India", 19.0760, 72.8777, "India", "Asia"),
    GazetteerEntry("Beijing", "Beijing, China", 39.9042, 116.4074, "China", "Asia"),
    GazetteerEntry("Shanghai", "Shanghai, China", 31.2304, 121.4737, "China", "Asia"),
    GazetteerEntry("Tokyo", "Tokyo, Japan", 35.6762, 139.6503, "Japan", "Asia"),
    GazetteerEntry("Jakarta", "Jakarta, Indonesia", -6.2088, 106.8456, "Indonesia", "Asia"),
    GazetteerEntry("Singapore", "Singapore", 1.3521, 103.8198, "Singapore", "Asia"),
    GazetteerEntry("Bangkok", "Bangkok, Thailand", 13.7563, 100.5018, "Thailand", "Asia"),
    GazetteerEntry("Seoul", "Seoul, South Korea", 37.5665, 126.9780, "South Korea", "Asia"),
    GazetteerEntry("Sydney", "Sydney, Australia", -33.8688, 151.2093, "Australia", "Oceania"),
    GazetteerEntry("Perth", "Perth, Australia", -31.9505, 115.8605, "Australia", "Oceania"),
    GazetteerEntry("Auckland", "Auckland, New Zealand", -36.8485, 174.7633, "New Zealand", "Oceania"),
    GazetteerEntry("Antarctica", "Vostok Station, Antarctica", -78.4645, 106.8334, "Antarctica", "Antarctica"),
]


def _search_offline(query: str, limit: int) -> list[LocationResult]:
    needle = query.strip().lower()
    if not needle:
        return []
    matches = [
        entry
        for entry in OFFLINE_GAZETTEER
        if needle in entry.name.lower()
        or needle in entry.display_name.lower()
        or needle in entry.country.lower()
        or needle in entry.region.lower()
    ]
    return [
        LocationResult(
            latitude=entry.latitude,
            longitude=entry.longitude,
            name=entry.name,
            display_name=entry.display_name,
            country=entry.country,
            region=entry.region,
            feature_type="city",
        )
        for entry in matches[:limit]
    ]


async def search_locations(query: str, limit: int = 8) -> LocationSearchResponse:
    """Search for locations, preferring the online geocoder."""
    offline = _search_offline(query, limit)
    try:
        params = {
            "q": query,
            "format": "jsonv2",
            "limit": limit,
            "addressdetails": 1,
        }
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                params=params,
                headers={"User-Agent": USER_AGENT},
            )
        if response.status_code == 200:
            results = []
            for item in response.json():
                address = item.get("address", {}) or {}
                results.append(
                    LocationResult(
                        latitude=float(item["lat"]),
                        longitude=float(item["lon"]),
                        name=item.get("name") or item.get("display_name", "").split(",")[0],
                        display_name=item.get("display_name", ""),
                        country=address.get("country"),
                        region=address.get("state") or address.get("region"),
                        feature_type=item.get("type"),
                    )
                )
            if results:
                return LocationSearchResponse(query=query, results=results, source="nominatim")
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        logger.info("Online geocoding unavailable (%s); using offline gazetteer.", exc)

    return LocationSearchResponse(query=query, results=offline, source="offline_gazetteer")
