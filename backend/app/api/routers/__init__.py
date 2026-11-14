"""API routers."""

from app.api.routers import (
    analysis,
    data,
    datasets,
    export,
    health,
    locations,
    variables,
)

__all__ = ["analysis", "data", "datasets", "export", "health", "locations", "variables"]
