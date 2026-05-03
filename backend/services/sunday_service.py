from typing import List

from core.supabase_client import get_supabase
from schemas.sunday import (
    SundayHistoryAllResponse,
    SundayHistoryItem,
    SundayShowItem,
)


_SUNDAY_TABLE = "calender_sunday"
_SUNDAY_COLS = "date, main_event, perks_text"

_SHOW_TABLE = "show_live"
_SHOW_COLS = "event, live_show_day, note"


def _row_to_history(row: dict) -> SundayHistoryItem:
    return SundayHistoryItem(
        date=str(row.get("date") or "")[:10],
        main_event=row.get("main_event") or "",
        perks_text=row.get("perks_text") or "",
    )


def _row_to_show(row: dict) -> SundayShowItem:
    return SundayShowItem(
        event=row.get("event") or "",
        live_show_day=str(row.get("live_show_day") or "")[:10],
        note=row.get("note") or "",
    )


def fetch_recent_history(limit: int = 5) -> List[SundayHistoryItem]:
    """홈 페이지: 최근 N주 이력 (최신순)."""
    sb = get_supabase()
    res = (
        sb.table(_SUNDAY_TABLE)
        .select(_SUNDAY_COLS)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return [_row_to_history(row) for row in (res.data or [])]


def fetch_all_history() -> SundayHistoryAllResponse:
    """캘린더 페이지: 썬데이 전체 이력 + 방송 일정 묶음."""
    sb = get_supabase()

    sunday_res = (
        sb.table(_SUNDAY_TABLE)
        .select(_SUNDAY_COLS)
        .order("date", desc=True)
        .execute()
    )
    show_res = (
        sb.table(_SHOW_TABLE)
        .select(_SHOW_COLS)
        .order("live_show_day", desc=True)
        .execute()
    )

    return SundayHistoryAllResponse(
        history=[_row_to_history(row) for row in (sunday_res.data or [])],
        shows=[_row_to_show(row) for row in (show_res.data or [])],
    )