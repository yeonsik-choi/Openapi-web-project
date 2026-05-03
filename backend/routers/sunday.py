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
from schemas.sunday import SundayHistoryItem, SundayRecentWithPredictionResponse
from services import sunday_service

router = APIRouter(prefix="/api/sunday", tags=["sunday"])


@router.get(
    "/history/recent",
    response_model=SundayRecentWithPredictionResponse,
    summary="최근 N주 썬데이 이력 + 최신 예측",
    description="홈 페이지. 응답 순서: prediction(최신 1건 상위 K) → history(ssunday 최근 N주).",
)
async def get_recent_history(
    limit: int = Query(6, ge=1, le=52, description="조회할 주 수 (ssunday)"),
    prediction_top_k: int = Query(
        5, ge=1, le=9, description="예측 카테고리 상위 개수 (probs 기준)"
    ),
):
    return await get_cache().get_or_set(
        key=k_sunday_recent(limit, prediction_top_k),
        fetcher=lambda: asyncio.to_thread(
            sunday_service.fetch_recent_with_prediction,
            history_limit=limit,
            prediction_top_k=prediction_top_k,
        ),
        ttl_sec=TTL_SUNDAY_RECENT,
    )


@router.get(
    "/history/all",
    response_model=List[SundayHistoryItem],
    summary="전체 썬데이 이력",
    description="캘린더 페이지에서 사용. 전체 이력 반환.",
)
async def get_all_history():
    return await get_cache().get_or_set(
        key=k_sunday_all(),
        fetcher=lambda: asyncio.to_thread(sunday_service.fetch_all_history),
        ttl_sec=TTL_SUNDAY_ALL,
        # 빈 리스트는 캐싱하지 않음 (Supabase 일시 오류 가드)
        skip_if=lambda r: not r,
    )