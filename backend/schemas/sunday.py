from pydantic import BaseModel, ConfigDict, Field


class SundayHistoryItem(BaseModel):
    """썬데이 이력 한 주."""

    model_config = ConfigDict(populate_by_name=True)

    date: str = Field(..., description="YYYY-MM-DD")
    main_event: str = Field("", serialization_alias="mainEvent")
    perks_text: str = Field("", serialization_alias="perksText")