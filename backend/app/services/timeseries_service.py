"""Time-series retrieval service.

Coordinates the provider, cache, and demonstration fallback to produce a
normalised observation series.  The service never fabricates data: when live
retrieval fails and no matching demonstration snapshot exists, the provider
error propagates to the caller.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from app.core.cache import FileCache, make_cache_key
from app.core.errors import ProviderError
from app.core.logging import get_logger
from app.providers.base import ProviderSeries
from app.providers.nasa_power import NasaPowerProvider
from app.services import demo_store
from app.services.climate_dataset_service import climate_dataset_service
from app.services.variable_registry import get_variable
from app.statistics.types import Series

logger = get_logger(__name__)


@dataclass
class TimeSeriesBundle:
    series: Series
    provider_series: ProviderSeries
    retrieval_mode: str
    warnings: list[str] = field(default_factory=list)
    cache_key: str = ""


def _series_to_cache_payload(series: ProviderSeries) -> dict:
    return {
        "variable_code": series.variable_code,
        "units": series.units,
        "longname": series.longname,
        "observations": [[d.isoformat(), v] for d, v in series.observations],
        "missing": [d.isoformat() for d in series.missing],
        "fill_value": series.fill_value,
        "request_url": series.request_url,
        "request_params": series.request_params,
        "source_name": series.source_name,
        "api_version": series.api_version,
        "notes": series.notes,
    }


def _payload_to_series(payload: dict) -> ProviderSeries:
    from app.core.timeutils import parse_iso_date

    return ProviderSeries(
        variable_code=payload["variable_code"],
        units=payload.get("units", ""),
        longname=payload.get("longname", ""),
        observations=[(parse_iso_date(item[0]), float(item[1])) for item in payload.get("observations", [])],
        missing=[parse_iso_date(item) for item in payload.get("missing", [])],
        fill_value=payload.get("fill_value"),
        request_url=payload.get("request_url", ""),
        request_params=payload.get("request_params", {}),
        source_name=payload.get("source_name", ""),
        api_version=payload.get("api_version", ""),
        retrieval_mode="cache",
        notes=payload.get("notes", []),
    )


class TimeSeriesService:
    def __init__(self, provider: NasaPowerProvider | None = None, cache: FileCache | None = None) -> None:
        self.provider = provider or NasaPowerProvider()
        self.cache = cache or FileCache()

    def _cache_key(self, **kwargs) -> str:
        return make_cache_key("power", kwargs)

    async def get_series(
        self,
        *,
        variable: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        frequency: str,
        allow_demo: bool = True,
    ) -> TimeSeriesBundle:
        definition = get_variable(variable, require_available=True)
        cache_params = {
            "provider": self.provider.name,
            "variable": definition.code,
            "latitude": round(latitude, 4),
            "longitude": round(longitude, 4),
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "frequency": frequency,
            "community": self.provider.community,
        }
        key = self._cache_key(**cache_params)

        cached = self.cache.get(key)
        if cached is not None:
            provider_series = _payload_to_series(cached)
            return self._finalise(provider_series, definition, "cache", frequency, key)

        # 1. Prefer verified local project dataset when using real NASA POWER provider
        if frequency == "monthly" and isinstance(self.provider, NasaPowerProvider):
            dataset_series = climate_dataset_service.get_series(
                variable=definition.code,
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
            )
            if dataset_series is not None:
                return self._finalise(dataset_series, definition, "dataset", frequency, key)

        warnings: list[str] = []
        try:
            provider_series = await self.provider.fetch_series(
                variable_code=definition.code,
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
                frequency=frequency,
            )
            self.cache.set(key, _series_to_cache_payload(provider_series))
            return self._finalise(provider_series, definition, "live", frequency, key)
        except ProviderError as exc:
            logger.warning("Live NASA POWER retrieval failed: %s", exc.message)
            if not allow_demo:
                raise
            sample = demo_store.find_sample(
                variable=definition.code,
                frequency=frequency,
                latitude=latitude,
                longitude=longitude,
                start_date=start_date,
                end_date=end_date,
            )
            if sample is None:
                raise ProviderError(
                    "Live NASA POWER data is currently unavailable and no demonstration "
                    "snapshot matches this request. Try again later or choose a location "
                    "covered by the demonstration datasets.",
                    details={"cause": exc.message},
                ) from exc
            provider_series = demo_store.sample_to_series(
                sample, start_date=start_date, end_date=end_date
            )
            warnings.append(
                "Serving a demonstration snapshot instead of live data. Results are "
                "real previously-retrieved NASA POWER values for the snapshot location."
            )
            bundle = self._finalise(provider_series, definition, "demo", frequency, key)
            bundle.warnings = warnings + bundle.warnings
            return bundle

    def _finalise(
        self,
        provider_series: ProviderSeries,
        definition,
        mode: str,
        frequency: str,
        key: str,
    ) -> TimeSeriesBundle:
        provider_series.retrieval_mode = mode
        dates = [d for d, _ in provider_series.observations]
        values = [v for _, v in provider_series.observations]
        series = Series(
            variable=definition.display_name,
            units=provider_series.units or definition.units,
            dates=dates,
            values=values,
            frequency=frequency,
        )
        warnings = list(provider_series.notes)
        return TimeSeriesBundle(
            series=series,
            provider_series=provider_series,
            retrieval_mode=mode,
            warnings=warnings,
            cache_key=key,
        )


timeseries_service = TimeSeriesService()
