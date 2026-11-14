"""Structured application errors.

Every error surfaced by the API carries a stable machine-readable ``code``
plus a human readable ``message`` and optional ``details`` so the frontend can
react deterministically instead of string-matching messages.
"""

from __future__ import annotations

from typing import Any


class EarthTrendError(Exception):
    """Base class for all expected application errors."""

    status_code: int = 500
    code: str = "internal_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_payload(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "details": self.details,
            }
        }


class ValidationError(EarthTrendError):
    status_code = 422
    code = "validation_error"


class NotFoundError(EarthTrendError):
    status_code = 404
    code = "not_found"


class UnsupportedVariableError(EarthTrendError):
    status_code = 400
    code = "unsupported_variable"


class ProviderError(EarthTrendError):
    """Upstream NASA service failure that could not be recovered."""

    status_code = 502
    code = "provider_error"


class ProviderTimeoutError(ProviderError):
    code = "provider_timeout"


class InsufficientDataError(EarthTrendError):
    """Not enough valid observations to run a meaningful analysis."""

    status_code = 422
    code = "insufficient_data"


class RateLimitError(EarthTrendError):
    status_code = 429
    code = "rate_limited"
