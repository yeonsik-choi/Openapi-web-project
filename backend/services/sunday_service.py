from typing import List

from core.supabase_client import get_supabase
from schemas.sunday import (
    SundayHistoryAllResponse,
    SundayHistoryItem,
    SundayShowItem,
    SundayUpdateItem
)


_SUNDAY_TABLE = "calender_sunday"
_SUNDAY_COLS = "date, main_event, perks_text"

_SHOW_TABLE = "show_live"
_SHOW_COLS = "event, live_show_day, note"

_UPDATE_TABLE = "update_event"
_UPDATE_COLS = "event, update_day, note"


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


def _row_to_update(row: dict) -> SundayUpdateItem:
    return SundayUpdateItem(
        event=row.get("event") or "",
        update_day=str(row.get("update_day") or "")[:10],
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
    sb = get_supabase()

    sunday_res = (
        sb.table(_SUNDAY_TABLE).select(_SUNDAY_COLS).order("date", desc=True).execute()
    )
    show_res = (
        sb.table(_SHOW_TABLE).select(_SHOW_COLS).order("live_show_day", desc=True).execute()
    )
    update_res = (
        sb.table(_UPDATE_TABLE).select(_UPDATE_COLS).order("update_day", desc=True).execute()
    )

    return SundayHistoryAllResponse(
        history=[_row_to_history(row) for row in (sunday_res.data or [])],
        shows=[_row_to_show(row) for row in (show_res.data or [])],
        updates=[_row_to_update(row) for row in (update_res.data or [])],
    )
