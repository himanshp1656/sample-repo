from __future__ import annotations
from typing import Optional
from db import DatabaseClient
from utils import enrich_user, format_user
from cache import cache_user, get_cached_user, cache_or_fetch
from errors import NotFoundError, safe_call
from analytics import track_metric
import time


class UserService:
    def __init__(self):
        self.db = DatabaseClient()
        self._request_count = 0

    def handle_request(self, user_id: int) -> str:
        start = time.time()
        self._request_count += 1
        user = self._load_user(user_id)
        enriched = enrich_user(user)
        result = format_user(enriched)
        elapsed = time.time() - start
        track_metric("request_duration_ms", elapsed * 1000)
        return result

    def _load_user(self, user_id: int) -> dict:
        cached = get_cached_user(user_id)
        if cached:
            return cached
        user = self.db.fetch_user(user_id)
        if not user:
            raise NotFoundError("User", user_id)
        cache_user(user_id, user)
        return user

    def get_user_safe(self, user_id: int) -> dict:
        return safe_call(self._load_user, user_id)

    def bulk_load(self, user_ids: list[int]) -> list[dict]:
        results = []
        for uid in user_ids:
            result = self.get_user_safe(uid)
            results.append({"user_id": uid, **result})
        return results

    def stats(self) -> dict:
        from analytics import get_metric_stats, rolling_average
        return {
            "requests_handled": self._request_count,
            "avg_duration_ms": rolling_average("request_duration_ms", window=100),
        }
