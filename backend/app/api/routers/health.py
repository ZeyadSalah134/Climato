"""Health and readiness endpoints."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import settings
from app.providers.nasa_power import nasa_power
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, summary="Service health")
async def health(check_provider: bool = False) -> HealthResponse:
    """Report service health.

    Set ``check_provider=true`` to perform a live reachability probe against
    NASA POWER (this adds a small amount of latency).
    """
    reachable: bool | None = None
    if check_provider:
        reachable = await nasa_power.health_check()

    status = "ok"
    if reachable is False:
        status = "degraded"

    return HealthResponse(
        status=status,  # type: ignore[arg-type]
        version=settings.app_version,
        engine_version=settings.analysis_engine_version,
        environment=settings.environment,
        cache_enabled=settings.cache_enabled,
        database=settings.database_url.split("://", 1)[0],
        provider_reachable=reachable,
        timestamp=datetime.now(timezone.utc),
    )
