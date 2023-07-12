import dataclasses
import random
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional

from aiogram.types import Chat, ChatMember

from yakusoku import database
from yakusoku.shared import users

DATABASE_NAME = "waifu"
WAIFU_MIN_RARITY = 1
WAIFU_MAX_RARITY = 10


@dataclass(frozen=True)
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
    married: Optional[int] = None

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


class WaifuState(Enum):
    NONE = auto()
    UPDATED = auto()
    MARRIED = auto()


@dataclass(frozen=True)
class WaifuInfo:
    member: ChatMember
    state: WaifuState


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

    def _is_choosable(self, chat: int, member: int) -> bool:
        return (
            property := self.get_waifu_property(chat, member)
        ).rarity != WAIFU_MAX_RARITY and property.married is None

    async def _random_waifu(self, chat: Chat, member: int) -> int:
        mapping = {
            waifu: property
            for waifu, property in self._get_waifu_property_map(chat.id).items()
            if member != waifu and self._is_choosable(chat.id, waifu)
        }
        try:
            return random.choices(
                list(mapping.keys()), [property.get_weight() for property in mapping.values()], k=1
            )[0]
        except IndexError:
            raise MemberNotEfficientError
        except ValueError:
            raise NoChoosableWaifuError

    def get_waifu_property(self, chat: int, member: int) -> WaifuProperty:
        data = self._get_waifu_property_db(chat).get(member)
        return WaifuProperty.from_database(data) if data else WaifuProperty()

    def update_waifu_property(self, chat: int, member: int, **changes: Any) -> None:
        db = self._get_waifu_property_db(chat)
        property = dataclasses.replace(self.get_waifu_property(chat, member), **changes)
        db[member] = property.to_database()

    def _is_update_needed(self, chat: int, data: _WaifuData) -> bool:
        return datetime.fromtimestamp(
            data.last
        ).date() < datetime.now().date() or not self._is_choosable(chat, data.member)

    def _update_waifu(self, chat: int, member: int, waifu: int) -> None:
        db = self._get_waifu_db(chat)
        data = _WaifuData(waifu, int(datetime.now().timestamp()))
        db[member] = data.to_database()

    async def fetch_waifu(self, chat: Chat, member: int) -> WaifuInfo:
        if married := self.get_waifu_property(chat.id, member).married:
            waifu = await chat.get_member(married)
            return WaifuInfo(waifu, WaifuState.MARRIED)
        if (data := self._get_waifu_data(chat.id, member)) and not self._is_update_needed(
            chat.id, data
        ):
            waifu = await chat.get_member(data.member)
            return WaifuInfo(waifu, WaifuState.NONE)

        waifu_id = await self._random_waifu(chat, member)
        self._update_waifu(chat.id, member, waifu_id)

        waifu = await chat.get_member(waifu_id)
        return WaifuInfo(waifu, WaifuState.UPDATED)

    def remove_waifu(self, chat: int, member: int) -> None:
        db = self._get_waifu_db(chat)
        del db[member]

    def remove_chat(self, chat: Chat) -> None:
        self._get_waifu_db(chat.id).clear()
        self._get_waifu_property_db(chat.id).clear()
