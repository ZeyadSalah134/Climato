"""File-based cache for retrieved scientific datasets.

The cache is intentionally simple: a JSON blob on disk keyed by a stable hash
of the request parameters. It stores the *raw* provider payload together with
retrieval metadata so provenance is never lost.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def make_cache_key(namespace: str, params: dict[str, Any]) -> str:
    canonical = json.dumps({"namespace": namespace, "params": params}, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:32]
    return f"{namespace}_{digest}"


class FileCache:
    """A tiny TTL cache backed by JSON files."""

    def __init__(self, directory: Path | None = None, ttl_seconds: int | None = None) -> None:
        self.directory = directory or settings.cache_dir
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds
        self.enabled = settings.cache_enabled
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.directory / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.enabled:
            return None
        path = self._path(key)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:  # pragma: no cover - defensive
            logger.warning("Discarding unreadable cache entry %s: %s", key, exc)
            return None

        stored_at = float(payload.get("_cached_at", 0))
        if self.ttl_seconds <= 0 or (time.time() - stored_at) > self.ttl_seconds:
            logger.debug("Cache entry %s expired", key)
            return None
        return payload

    def set(self, key: str, value: dict[str, Any]) -> None:
        if not self.enabled:
            return
        payload = dict(value)
        payload["_cached_at"] = time.time()
        path = self._path(key)
        tmp = path.with_suffix(".tmp")
        try:
            tmp.write_text(json.dumps(payload), encoding="utf-8")
            tmp.replace(path)
        except OSError as exc:  # pragma: no cover - defensive
            logger.warning("Failed to write cache entry %s: %s", key, exc)

    def clear(self) -> int:
        count = 0
        for item in self.directory.glob("*.json"):
            try:
                item.unlink()
                count += 1
            except OSError:  # pragma: no cover - defensive
                pass
        return count


cache = FileCache()
