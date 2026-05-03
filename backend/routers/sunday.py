import asyncio
from typing import List

from fastapi import APIRouter, Query

from core.cache import get_cache
from core.cache_keys import (
    TTL_SUNDAY_ALL,
    TTL_SUNDAY_RECENT,
    k_sunday_all,
    k_sunday_recent,
)
from schemas.sunday import SundayHistoryItem
from services import sunday_service

router = APIRouter(prefix="/api/sunday", tags=["sunday"])


@router.get(
    "/history/recent",
    response_model=List[SundayHistoryItem],
    response_model_by_alias=True,
    summary="최근 N주 썬데이 이력",
    description="홈 페이지. calender_sunday 최신순 N주 반환.",
)
async def get_recent_history(
    limit: int = Query(5, ge=1, le=52, description="조회할 주 수"),
):
    return await get_cache().get_or_set(
        key=k_sunday_recent(limit),
        fetcher=lambda: asyncio.to_thread(
            sunday_service.fetch_recent_history,
            limit=limit,
        ),
        ttl_sec=TTL_SUNDAY_RECENT,
        # 빈 리스트는 캐싱하지 않음 (Supabase 일시 오류 가드)
        skip_if=lambda r: not r,
    )


@router.get(
    "/history/all",
    response_model=List[SundayHistoryItem],
    response_model_by_alias=True,
    summary="전체 썬데이 이력",
    description="캘린더 페이지. calender_sunday 전체 최신순 반환.",
)
async def get_all_history():
    return await get_cache().get_or_set(
        key=k_sunday_all(),
        fetcher=lambda: asyncio.to_thread(sunday_service.fetch_all_history),
        ttl_sec=TTL_SUNDAY_ALL,
        skip_if=lambda r: not r,
    )