import asyncio

from fastapi import APIRouter

from core.cache import get_cache
from core.cache_keys import (
    TTL_SUNDAY_ALL,
    k_sunday_all,
)
from schemas.sunday import SundayHistoryAllResponse
from services import sunday_service

router = APIRouter(prefix="/api/sunday", tags=["sunday"])


@router.get(
    "/history/all",
    response_model=SundayHistoryAllResponse,
    response_model_by_alias=True,
    summary="전체 썬데이 이력 + 방송 일정",
    description="캘린더 페이지. calender_sunday 전체(최신순) + show_live 전체.",
)
async def get_all_history():
    return await get_cache().get_or_set(
        key=k_sunday_all(),
        fetcher=lambda: asyncio.to_thread(sunday_service.fetch_all_history),
        ttl_sec=TTL_SUNDAY_ALL,
        # 두 배열 모두 비어있을 때만 캐싱 안 함
        skip_if=lambda r: not r.history and not r.shows and not r.updates,
    )
