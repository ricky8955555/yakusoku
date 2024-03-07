from datetime import datetime

from pydantic import validator
from sqlmodel import Field, SQLModel

WAIFU_MIN_RARITY = 1
WAIFU_MAX_RARITY = 10
WAIFU_DEFAULT_RARITY = 5


class WaifuData(SQLModel, table=True):
    group: int = Field(primary_key=True)
    member: int = Field(primary_key=True)
    waifu: int | None = None
    modified: datetime | None = None
    restricted: bool = False
    rarity: int = WAIFU_DEFAULT_RARITY

    def get_partner(self) -> int | None:
        assert not self.restricted or self.waifu, "no waifu when restricted is true."
        return self.waifu if self.restricted else None

    def set_partner(self, value: int | None) -> None:
        self.waifu = value
        self.restricted = value is not None

    def get_weight(self) -> int:
        return WAIFU_MAX_RARITY - self.rarity

    @validator("rarity")
    def rarity_validate(cls, value: int) -> int:
        assert WAIFU_MIN_RARITY <= value <= WAIFU_MAX_RARITY, "invalid rarity"
        return value


class WaifuConfig(SQLModel, table=True):
    user: int = Field(primary_key=True)
    mentionable: bool = False
