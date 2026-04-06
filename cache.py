from __future__ import annotations
import time
from typing import Any, Optional

# Module-level cache store
_cache: dict[str, Any] = {}
_expiry: dict[str, float] = {}
_hit_count: dict[str, int] = {}

DEFAULT_TTL = 300  # 5 minutes


def set_cache(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    _cache[key] = value
    _expiry[key] = time.time() + ttl
    _hit_count.setdefault(key, 0)


def is_expired(key: str) -> bool:
    if key not in _expiry:
        return True
    return time.time() > _expiry[key]


def get_cache(key: str) -> Optional[Any]:
    if key not in _cache or is_expired(key):
        return None
    _hit_count[key] = _hit_count.get(key, 0) + 1
    return _cache[key]


def invalidate(key: str) -> bool:
    existed = key in _cache
    _cache.pop(key, None)
    _expiry.pop(key, None)
    return existed


def invalidate_prefix(prefix: str) -> int:
    keys = [k for k in _cache if k.startswith(prefix)]
    for k in keys:
        invalidate(k)
    return len(keys)


def clear_all() -> int:
    count = len(_cache)
    _cache.clear()
    _expiry.clear()
    _hit_count.clear()
    return count


def cache_stats() -> dict:
    total = len(_cache)
    expired = sum(1 for k in _cache if is_expired(k))
    return {
        "total_keys": total,
        "live_keys": total - expired,
        "expired_keys": expired,
        "total_hits": sum(_hit_count.values()),
    }


def cache_user(user_id: int, data: dict, ttl: int = DEFAULT_TTL) -> None:
    set_cache(f"user:{user_id}", data, ttl)


def get_cached_user(user_id: int) -> Optional[dict]:
    return get_cache(f"user:{user_id}")


def cache_or_fetch(key: str, fetch_fn, ttl: int = DEFAULT_TTL) -> Any:
    cached = get_cache(key)
    if cached is not None:
        return cached
    value = fetch_fn()
    set_cache(key, value, ttl)
    return value
