from datetime import datetime
from typing import Optional

from pydantic import validator
from sqlmodel import Field, SQLModel

WAIFU_MIN_RARITY = 1
WAIFU_MAX_RARITY = 10
WAIFU_DEFAULT_RARITY = 5


class WaifuData(SQLModel, table=True):
    group: int = Field(primary_key=True)
    member: int = Field(primary_key=True)
    waifu: Optional[int] = None
    modified: Optional[datetime] = None
    forced: bool = False
    rarity: int = WAIFU_DEFAULT_RARITY

    @property
    def partner(self) -> Optional[int]:
        assert not self.forced or self.waifu, "no waifu when forced is true."
        return self.waifu if self.forced else None

    @partner.setter
    def partner(self, value: Optional[int]) -> None:
        self.waifu = value
        self.forced = value is not None

    def get_weight(self) -> int:
        return WAIFU_MAX_RARITY - self.rarity

    @validator("rarity")
    def rarity_validate(cls, value: int) -> int:
        assert WAIFU_MIN_RARITY < value < WAIFU_MAX_RARITY, "invalid rarity"
        return value


class WaifuConfig(SQLModel, table=True):
    user: int = Field(primary_key=True)
    mentionable: bool = False