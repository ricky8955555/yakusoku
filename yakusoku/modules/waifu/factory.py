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
class WaifuGlobalProperty:
    mentionable: bool = False

    @staticmethod
    def from_database(data: tuple[Any, ...]) -> "WaifuGlobalProperty":
        return WaifuGlobalProperty(*data)

    def to_database(self) -> tuple[Any, ...]:
        return dataclasses.astuple(self)


@dataclass(frozen=True)
class WaifuLocalProperty:
    rarity: int = WAIFU_MIN_RARITY
    married: Optional[int] = None
    mentionable: Optional[bool] = None

    def __post_init__(self):
        if not WaifuLocalProperty.is_valid_rarity(self.rarity):
            raise ValueError("rarity is out of range")

    @staticmethod
    def from_database(data: tuple[Any, ...]) -> "WaifuLocalProperty":
        return WaifuLocalProperty(*data)

    def to_database(self) -> tuple[Any, ...]:
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
    _local_properties: dict[int, dict[int, tuple[Any, ...]]]
    _global_properties: dict[int, tuple[Any, ...]]

    def __init__(self) -> None:
        self._waifus = {}
        self._local_properties = {}
        self._global_properties = database.get(DATABASE_NAME, "property")

    def _get_waifu_db(self, chat: int) -> dict[int, tuple[int, int]]:
        if not (db := self._waifus.get(chat)):
            db = self._waifus[chat] = database.get(DATABASE_NAME, f"waifu_{chat}")
        return db

    def _get_waifu_local_property_db(self, chat: int) -> dict[int, tuple[int]]:
        if not (db := self._local_properties.get(chat)):
            db = self._local_properties[chat] = database.get(DATABASE_NAME, f"property_{chat}")
        return db

    def _get_waifu_data(self, chat: int, member: int) -> _WaifuData | None:
        data = self._get_waifu_db(chat).get(member)
        return _WaifuData.from_database(data) if data else None

    def _is_choosable(self, chat: int, member: int) -> bool:
        return (
            property := self.get_waifu_local_property(chat, member)
        ).rarity < WAIFU_MAX_RARITY and property.married is None

    async def _random_waifu(self, chat: Chat, member: int) -> int:
        mapping = {
            waifu: self.get_waifu_local_property(chat.id, waifu).get_weight()
            for waifu in users.get_members(chat.id)
            if member != waifu and self._is_choosable(chat.id, waifu)
        }
        try:
            return random.choices(
                list(mapping.keys()), [weight for weight in mapping.values()], k=1
            )[0]
        except IndexError:
            raise MemberNotEfficientError
        except ValueError:
            raise NoChoosableWaifuError

    def get_waifu_local_property(self, chat: int, member: int) -> WaifuLocalProperty:
        data = self._get_waifu_local_property_db(chat).get(member)
        return WaifuLocalProperty.from_database(data) if data else WaifuLocalProperty()

    def update_waifu_local_property(self, chat: int, member: int, **changes: Any) -> None:
        db = self._get_waifu_local_property_db(chat)
        property = dataclasses.replace(self.get_waifu_local_property(chat, member), **changes)
        db[member] = property.to_database()

    def get_waifu_global_property(self, user: int) -> WaifuGlobalProperty:
        data = self._global_properties.get(user)
        return WaifuGlobalProperty.from_database(data) if data else WaifuGlobalProperty()

    def update_waifu_global_property(self, user: int, **changes: Any) -> None:
        property = dataclasses.replace(self.get_waifu_global_property(user), **changes)
        self._global_properties[user] = property.to_database()

    def _is_update_needed(self, chat: int, data: _WaifuData) -> bool:
        return datetime.fromtimestamp(
            data.last
        ).date() < datetime.now().date() or not self._is_choosable(chat, data.member)

    def _update_waifu(self, chat: int, member: int, waifu: int) -> None:
        db = self._get_waifu_db(chat)
        data = _WaifuData(waifu, int(datetime.now().timestamp()))
        db[member] = data.to_database()

    async def fetch_waifu(self, chat: Chat, member: int) -> WaifuInfo:
        if married := self.get_waifu_local_property(chat.id, member).married:
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

    def remove_chat(self, chat: int) -> None:
        self._get_waifu_db(chat).clear()
        self._get_waifu_local_property_db(chat).clear()
