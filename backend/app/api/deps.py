"""API dependencies: rate limiting and shared helpers."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import settings
from app.core.errors import RateLimitError

# In-memory sliding-window rate limiter.  Adequate for a single-process
# deployment; a multi-instance deployment should use a shared store.
_WINDOWS: dict[str, deque[float]] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    """Sliding-window rate limit keyed by client host."""
    limit = settings.rate_limit_requests
    window = settings.rate_limit_window_seconds
    if limit <= 0:
        return
    client = request.client.host if request.client else "unknown"
    now = time.time()
    bucket = _WINDOWS[client]
    while bucket and (now - bucket[0]) > window:
        bucket.popleft()
    if len(bucket) >= limit:
        raise RateLimitError(
            "Too many requests. Please slow down.",
            details={"limit": limit, "window_seconds": window},
        )
    bucket.append(now)


def get_allow_demo(request: Request) -> bool:
    """Resolve whether demonstration fallback is permitted for this request."""
    if not settings.allow_demo_fallback:
        return False
    param = request.query_params.get("allow_demo")
    if param is None:
        return True
    return param.lower() not in {"false", "0", "no"}
