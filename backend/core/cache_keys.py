"""캐시 키/TTL 중앙 관리.

캐시 정책 변경 시 이 파일만 수정하면 됨.
"""
from __future__ import annotations


# ─────────────────── TTL ───────────────────
TTL_NOTICES = 1800       # 30분: 공지 갱신 빈도 낮음
TTL_SUNDAY_ALL = 3600    # 1시간: 캘린더 풀 히스토리, 일요일에만 추가됨


# ─────────────────── 키 ───────────────────
def k_notices() -> str:
    return "notices:all"


def k_sunday_all() -> str:
    return "sunday:all"