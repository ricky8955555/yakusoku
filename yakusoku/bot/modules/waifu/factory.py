import contextlib
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Iterable

from aiogram.types import Chat, ChatMember

from ... import database
from ...shared import users

DATABASE_NAME = "waifu"


@dataclass
class _WaifuData:
    member: int
    last: int

    @staticmethod
    def from_database(data: tuple[Any, ...]) -> "_WaifuData":
        return _WaifuData(*data)

    def to_database(self) -> tuple[int, int]:
        return (self.member, self.last)


class WaifuFactory:
    _waifus: dict[int, dict[int, tuple[int, int]]]
    _forbidden: dict[int, set[int]]

    def __init__(self) -> None:
        self._waifus = {}
        self._forbidden = database.get(DATABASE_NAME, "forbidden")

    def _get_waifu_db(self, chat: int) -> dict[int, tuple[int, int]]:
        if not (db := self._waifus.get(chat)):
            db = self._waifus[chat] = database.get(DATABASE_NAME, f"waifu_{chat}")
        return db

    def _get_waifu_data(self, chat: int, member: int) -> _WaifuData | None:
        data = self._get_waifu_db(chat).get(member)
        return _WaifuData.from_database(data) if data else None

    def _allowed_waifu(self, chat: int) -> Iterable[int]:
        forbidden = self.get_forbidden_waifu(chat)
        return (member for member in users.get_members(chat) if member not in forbidden)

    async def _random_waifu(self, chat: Chat) -> tuple[_WaifuData, ChatMember]:
        member = random.choice(list(self._allowed_waifu(chat.id)))
        member = await chat.get_member(member)
        data = _WaifuData(member.user.id, int(datetime.now().timestamp()))
        return (data, member)

    def forbid_waifu(self, chat: int, member: int) -> None:
        forbidden = self._forbidden.get(chat) or set()
        forbidden.add(member)
        self._forbidden[chat] = forbidden

    def allow_waifu(self, chat: int, member: int) -> None:
        with contextlib.suppress(KeyError):
            forbidden = self._forbidden[chat]
            forbidden.remove(member)
            self._forbidden[chat] = forbidden

    def get_forbidden_waifu(self, chat: int) -> set[int]:
        return self._forbidden.get(chat) or set()

    async def fetch_waifu(self, chat: Chat, member: int) -> tuple[bool, ChatMember]:
        data = self._get_waifu_data(chat.id, member)
        now = datetime.now()

        if not data or datetime.fromtimestamp(data.last).date() < now.date():
            db = self._get_waifu_db(chat.id)
            data, waifu = await self._random_waifu(chat)
            db[member] = data.to_database()
            return True, waifu
        else:
            waifu = await chat.get_member(data.member)
            return False, waifu

    def remove_chat(self, chat: Chat) -> None:
        self._get_waifu_db(chat.id).clear()
        with contextlib.suppress(KeyError):
            del self._forbidden[chat.id]
