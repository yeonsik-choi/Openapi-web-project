"""간단한 in-memory TTL 캐시.

- 프로세스 1개 단위로 동작 (Render 단일 인스턴스 환경에 적합)
- 재시작 시 캐시 초기화됨
- thread-safe (asyncio.Lock 사용)
- 만료 항목은 lazy 방식으로 정리 (조회 시점에 만료 확인)
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

logger = logging.getLogger(__name__)


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

    async def get_or_set(
        self,
        key: str,
        fetcher: Callable[[], Awaitable[Any]],
        ttl_sec: float,
        *,
        skip_if: Callable[[Any], bool] | None = None,
    ) -> Any:
        """캐시에 있으면 반환, 없으면 fetcher 실행 후 저장.

        - fetcher: 캐시 미스 시 호출할 async 함수 (인자 없음, lambda로 감싸 사용)
        - skip_if: 결과가 이 조건을 만족하면 캐시에 저장하지 않음 (부분 실패 가드용)
        """
        cached = await self.get(key)
        if cached is not None:
            logger.info("cache hit: %s", key)
            return cached

        result = await fetcher()
        if skip_if is None or not skip_if(result):
            await self.set(key, result, ttl_sec)
        return result


# 전역 캐시 인스턴스 (프로세스당 1개)
_global_cache = TTLCache()


def get_cache() -> TTLCache:
    """앱 전역에서 공유하는 캐시 반환."""
    return _global_cache