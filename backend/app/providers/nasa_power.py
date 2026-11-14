"""NASA POWER data provider adapter.

Implements the documented POWER temporal point endpoints:

* Monthly: https://power.larc.nasa.gov/docs/services/api/temporal/monthly/
* Daily:   https://power.larc.nasa.gov/docs/services/api/temporal/daily/

The adapter is responsible for:

1. Validating inputs.
2. Issuing the upstream request with retries and timeouts.
3. Parsing the POWER ``Feature`` JSON envelope.
4. Excluding documented fill values (``-999``).
5. Normalising keys (``YYYYMM`` monthly, ``YYYYMMDD`` daily) to real dates.
6. Preserving provider units and provenance metadata.

It never invents data: if the upstream service cannot be reached the adapter
raises :class:`ProviderError`.
"""

from __future__ import annotations

import asyncio
from datetime import date
from typing import Any

import httpx

from app.core.config import settings
from app.core.errors import ProviderError, ProviderTimeoutError
from app.core.logging import get_logger
from app.core.timeutils import month_end
from app.providers.base import ProviderSeries

logger = get_logger(__name__)


class NasaPowerProvider:
    """Adapter for the NASA POWER temporal point API."""

    name = "NASA_POWER"

    def __init__(
        self,
        base_url: str | None = None,
        community: str | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
    ) -> None:
        self.base_url = (base_url or settings.power_base_url).rstrip("/")
        self.community = community or settings.power_community
        self.timeout = timeout or settings.power_timeout_seconds
        self.max_retries = max_retries if max_retries is not None else settings.power_max_retries

    # -- public API --------------------------------------------------------
    async def fetch_series(
        self,
        *,
        variable_code: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        frequency: str,
    ) -> ProviderSeries:
        if frequency not in ("monthly", "daily"):
            raise ProviderError(f"Unsupported frequency '{frequency}' for NASA POWER.")

        params = self._build_params(
            variable_code=variable_code,
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
        )
        url = f"{self.base_url}/{frequency}/point"
        payload = await self._request(url, params)
        return self._parse(payload, variable_code, frequency, url, params)

    async def health_check(self) -> bool:
        """Lightweight reachability probe used by the health endpoint."""
        params = {
            "parameters": "T2M",
            "community": self.community,
            "latitude": 0.0,
            "longitude": 0.0,
            "start": "202001",
            "end": "202001",
            "format": "JSON",
        }
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(f"{self.base_url}/monthly/point", params=params)
            return response.status_code == 200
        except Exception:  # pragma: no cover - network dependent
            return False

    # -- internals ---------------------------------------------------------
    def _build_params(
        self,
        *,
        variable_code: str,
        latitude: float,
        longitude: float,
        start_date: date,
        end_date: date,
        frequency: str,
    ) -> dict[str, str]:
        if frequency == "monthly":
            start = f"{start_date.year:04d}{start_date.month:02d}"
            end = f"{end_date.year:04d}{end_date.month:02d}"
        else:
            start = f"{start_date.year:04d}{start_date.month:02d}{start_date.day:02d}"
            end = f"{end_date.year:04d}{end_date.month:02d}{end_date.day:02d}"
        return {
            "parameters": variable_code,
            "community": self.community,
            "longitude": f"{longitude:.4f}",
            "latitude": f"{latitude:.4f}",
            "start": start,
            "end": end,
            "format": "JSON",
        }

    async def _request(self, url: str, params: dict[str, str]) -> dict[str, Any]:
        last_error: Exception | None = None
        for attempt in range(1, self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.get(url, params=params)
                if response.status_code == 429:
                    raise ProviderError(
                        "NASA POWER rate limit reached. Please retry shortly.",
                        details={"status": 429},
                    )
                if response.status_code >= 500:
                    raise ProviderError(
                        f"NASA POWER returned server error {response.status_code}.",
                        details={"status": response.status_code},
                    )
                if response.status_code != 200:
                    raise ProviderError(
                        f"NASA POWER rejected the request (HTTP {response.status_code}).",
                        details={"status": response.status_code, "body": response.text[:300]},
                    )
                return response.json()
            except httpx.TimeoutException as exc:
                last_error = exc
                logger.warning("NASA POWER timeout (attempt %s/%s)", attempt, self.max_retries)
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning("NASA POWER transport error (attempt %s/%s): %s", attempt, self.max_retries, exc)
            except ProviderError:
                raise
            if attempt < self.max_retries:
                await asyncio.sleep(settings.power_retry_backoff_seconds * attempt)

        if isinstance(last_error, httpx.TimeoutException):
            raise ProviderTimeoutError(
                "NASA POWER did not respond within the timeout window.",
                details={"url": url, "params": params},
            )
        raise ProviderError(
            "Unable to reach NASA POWER after repeated attempts.",
            details={"url": url, "reason": str(last_error)},
        )

    def _parse(
        self,
        payload: dict[str, Any],
        variable_code: str,
        frequency: str,
        url: str,
        params: dict[str, str],
    ) -> ProviderSeries:
        header = payload.get("header", {}) or {}
        parameters = payload.get("parameters", {}) or {}
        properties = payload.get("properties", {}) or {}
        parameter_block = (properties.get("parameter") or {}).get(variable_code)

        if parameter_block is None:
            messages = payload.get("messages") or []
            raise ProviderError(
                f"NASA POWER returned no data for parameter '{variable_code}'.",
                details={"messages": messages, "params": params},
            )

        meta = parameters.get(variable_code, {}) or {}
        units = meta.get("units", "")
        longname = meta.get("longname", variable_code)
        fill_value = header.get("fill_value", -999.0)

        observations: list[tuple[date, float]] = []
        missing: list[date] = []

        for key, raw_value in parameter_block.items():
            if frequency == "monthly" and key.endswith("13"):
                # POWER monthly responses append month 13 = annual mean.
                # Including it alongside monthly values would double count.
                continue
            parsed_date = self._parse_key(key, frequency)
            if parsed_date is None:
                continue
            value = self._coerce(raw_value, fill_value)
            if value is None:
                missing.append(parsed_date)
            else:
                observations.append((parsed_date, value))

        observations.sort(key=lambda item: item[0])
        missing.sort()

        notes: list[str] = []
        messages = payload.get("messages") or []
        for message in messages:
            if isinstance(message, dict):
                notes.append(str(message.get("message", message)))
            else:
                notes.append(str(message))

        return ProviderSeries(
            variable_code=variable_code,
            units=units,
            longname=longname,
            observations=observations,
            missing=missing,
            fill_value=fill_value,
            request_url=url,
            request_params=params,
            source_name=", ".join(header.get("sources", [])) or "NASA POWER",
            api_version=(header.get("api") or {}).get("version", ""),
            retrieval_mode="live",
            notes=notes,
        )

    @staticmethod
    def _coerce(raw_value: Any, fill_value: float | None) -> float | None:
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            return None
        if fill_value is not None and abs(value - fill_value) < 1e-9:
            return None
        return value

    @staticmethod
    def _parse_key(key: str, frequency: str) -> date | None:
        text = str(key).strip()
        try:
            if frequency == "monthly":
                if len(text) < 6 or not text[:6].isdigit():
                    return None
                year, month = int(text[:4]), int(text[4:6])
                if not 1 <= month <= 12:
                    return None
                return month_end(year, month)
            if len(text) < 8 or not text[:8].isdigit():
                return None
            return date(int(text[:4]), int(text[4:6]), int(text[6:8]))
        except ValueError:
            return None


nasa_power = NasaPowerProvider()
