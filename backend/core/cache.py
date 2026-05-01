"""간단한 in-memory TTL 캐시.

- 프로세스 1개 단위로 동작 (Render 단일 인스턴스 환경에 적합)
- 재시작 시 캐시 초기화됨
- thread-safe (asyncio.Lock 사용)
- 만료 항목은 lazy 방식으로 정리 (조회 시점에 만료 확인)
"""
from __future__ import annotations

import asyncio
import time
from typing import Any


class TTLCache:
    """key별로 (value, expires_at) 저장. 조회 시 만료된 항목은 자동 삭제."""

    def __init__(self) -> None:
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        async with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if time.time() >= expires_at:
                # 만료됨 → 삭제하고 None 반환
                self._store.pop(key, None)
                return None
            return value

    async def set(self, key: str, value: Any, ttl_sec: float) -> None:
        async with self._lock:
            self._store[key] = (value, time.time() + ttl_sec)

    async def clear(self) -> None:
        async with self._lock:
            self._store.clear()

    async def size(self) -> int:
        """현재 저장된 항목 수 (만료 여부 무관). 디버깅용."""
        async with self._lock:
            return len(self._store)


# 전역 캐시 인스턴스 (프로세스당 1개)
_global_cache = TTLCache()


def get_cache() -> TTLCache:
    """앱 전역에서 공유하는 캐시 반환."""
    return _global_cache
