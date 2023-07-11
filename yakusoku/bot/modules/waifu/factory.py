import dataclasses
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from aiogram.types import Chat, ChatMember

from ... import database
from ...shared import users

DATABASE_NAME = "waifu"
WAIFU_MIN_RARITY = 1
WAIFU_MAX_RARITY = 10


@dataclass
class _WaifuData:
    member: int
    last: int

    @staticmethod
    def from_database(data: tuple[Any, ...]) -> "_WaifuData":
        return _WaifuData(*data)

    def to_database(self) -> tuple[int, int]:
        return dataclasses.astuple(self)


@dataclass(frozen=True)
class WaifuProperty:
    rarity: int = WAIFU_MIN_RARITY

    def __post_init__(self):
        if not WaifuProperty.is_valid_rarity(self.rarity):
            raise ValueError("rarity is out of range")

    @staticmethod
    def from_database(data: tuple[Any, ...]) -> "WaifuProperty":
        return WaifuProperty(*data)

    def to_database(self) -> tuple[int]:
        return dataclasses.astuple(self)

    def get_weight(self) -> float:
        return (10 - self.rarity) / 10

    @staticmethod
    def is_valid_rarity(value: int) -> bool:
        return WAIFU_MIN_RARITY <= value <= WAIFU_MAX_RARITY


class MemberNotEfficientError(Exception):
    pass


class NoChoosableWaifuError(Exception):
    pass


class WaifuFactory:
    _waifus: dict[int, dict[int, tuple[int, int]]]
    _properties: dict[int, dict[int, tuple[int]]]

    def __init__(self) -> None:
        self._waifus = {}
        self._properties = {}

    def _get_waifu_db(self, chat: int) -> dict[int, tuple[int, int]]:
        if not (db := self._waifus.get(chat)):
            db = self._waifus[chat] = database.get(DATABASE_NAME, f"waifu_{chat}")
        return db

    def _get_waifu_property_db(self, chat: int) -> dict[int, tuple[int]]:
        if not (db := self._properties.get(chat)):
            db = self._properties[chat] = database.get(DATABASE_NAME, f"property_{chat}")
        return db

    def _get_waifu_data(self, chat: int, member: int) -> _WaifuData | None:
        data = self._get_waifu_db(chat).get(member)
        return _WaifuData.from_database(data) if data else None

    def _get_waifu_property_map(self, chat: int) -> dict[int, WaifuProperty]:
        return {member: self.get_waifu_property(chat, member) for member in users.get_members(chat)}

    async def _random_waifu(self, chat: Chat, member: int) -> tuple[_WaifuData, ChatMember]:
        mapping = {
            waifu: property
            for waifu, property in self._get_waifu_property_map(chat.id).items()
            if member != waifu
        }
        try:
            members = random.choices(
                list(mapping.keys()), [property.get_weight() for property in mapping.values()], k=1
            )
        except IndexError:
            raise MemberNotEfficientError
        except ValueError:
            raise NoChoosableWaifuError
        waifu = await chat.get_member(members[0])
        data = _WaifuData(waifu.user.id, int(datetime.now().timestamp()))
        return (data, waifu)

    def get_waifu_property(self, chat: int, member: int) -> WaifuProperty:
        data = self._get_waifu_property_db(chat).get(member)
        return WaifuProperty.from_database(data) if data else WaifuProperty()

    def set_waifu_property(self, chat: int, member: int, property: WaifuProperty) -> None:
        db = self._get_waifu_property_db(chat)
        db[member] = property.to_database()

    async def fetch_waifu(self, chat: Chat, member: int) -> tuple[bool, ChatMember]:
        data = self._get_waifu_data(chat.id, member)
        now = datetime.now()

        if (
            not data
            or datetime.fromtimestamp(data.last).date() < now.date()
            or self.get_waifu_property(chat.id, data.member).rarity == WAIFU_MAX_RARITY
        ):
            db = self._get_waifu_db(chat.id)
            data, waifu = await self._random_waifu(chat, member)
            db[member] = data.to_database()
            return True, waifu
        else:
            waifu = await chat.get_member(data.member)
            return False, waifu

    def remove_chat(self, chat: Chat) -> None:
        self._get_waifu_db(chat.id).clear()
        self._get_waifu_property_db(chat.id).clear()
