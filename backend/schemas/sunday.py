from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SundayHistoryItem(BaseModel):
    """썬데이 이력 한 주."""

    model_config = ConfigDict(populate_by_name=True)

    date: str = Field(..., description="YYYY-MM-DD")
    main_event: str = Field("", serialization_alias="mainEvent")
    perks_text: str = Field("", serialization_alias="perksText")


class SundayShowItem(BaseModel):
    """방송/라이브 일정 한 건."""

    model_config = ConfigDict(populate_by_name=True)

    event: str = ""
    live_show_day: str = Field("", serialization_alias="liveShowDay", description="YYYY-MM-DD")
    note: str = ""


class SundayHistoryAllResponse(BaseModel):
    """캘린더 페이지: 썬데이 이력 + 방송 일정."""

    model_config = ConfigDict(populate_by_name=True)

    history: List[SundayHistoryItem]
    shows: List[SundayShowItem]