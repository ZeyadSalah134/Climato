"""File cache tests."""

from __future__ import annotations

from pathlib import Path

from app.core.cache import FileCache, make_cache_key


def test_cache_round_trip(tmp_path: Path) -> None:
    cache = FileCache(directory=tmp_path, ttl_seconds=60)
    cache.enabled = True
    cache.set("key1", {"value": 42})
    loaded = cache.get("key1")
    assert loaded is not None
    assert loaded["value"] == 42
    assert "_cached_at" in loaded


def test_cache_miss_returns_none(tmp_path: Path) -> None:
    cache = FileCache(directory=tmp_path, ttl_seconds=60)
    cache.enabled = True
    assert cache.get("absent") is None


def test_cache_expiry(tmp_path: Path) -> None:
    cache = FileCache(directory=tmp_path, ttl_seconds=-1)
    cache.enabled = True
    cache.set("key2", {"value": 1})
    assert cache.get("key2") is None


def test_cache_clear(tmp_path: Path) -> None:
    cache = FileCache(directory=tmp_path, ttl_seconds=60)
    cache.enabled = True
    cache.set("a", {"v": 1})
    cache.set("b", {"v": 2})
    assert cache.clear() == 2
    assert cache.get("a") is None


def test_cache_key_is_stable_and_order_independent() -> None:
    key1 = make_cache_key("ns", {"a": 1, "b": 2})
    key2 = make_cache_key("ns", {"b": 2, "a": 1})
    assert key1 == key2
    assert key1 != make_cache_key("ns", {"a": 1, "b": 3})
