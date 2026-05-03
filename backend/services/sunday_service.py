from typing import List

from core.supabase_client import get_supabase
from schemas.sunday import SundayHistoryItem


_TABLE = "calender_sunday"
_COLS = "date, main_event, perks_text"


def _row_to_item(row: dict) -> SundayHistoryItem:
    return SundayHistoryItem(
        date=str(row.get("date") or "")[:10],
        main_event=row.get("main_event") or "",
        perks_text=row.get("perks_text") or "",
    )


def fetch_recent_history(limit: int = 5) -> List[SundayHistoryItem]:
    """홈 페이지: 최근 N주 이력 (최신순)."""
    sb = get_supabase()
    res = (
        sb.table(_TABLE)
        .select(_COLS)
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return [_row_to_item(row) for row in (res.data or [])]


def fetch_all_history() -> List[SundayHistoryItem]:
    """캘린더 페이지: 전체 이력 (최신순)."""
    sb = get_supabase()
    res = (
        sb.table(_TABLE)
        .select(_COLS)
        .order("date", desc=True)
        .execute()
    )
    return [_row_to_item(row) for row in (res.data or [])]