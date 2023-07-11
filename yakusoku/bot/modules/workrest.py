import dataclasses
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from aiogram.types import Message

from .. import database
from . import command_handler

db: dict[int, tuple[bool, int]] = database.get("workrest", "workrest")


@dataclass(frozen=True)
class UserInfo:
    awake: bool
    last: int

    @staticmethod
    def from_database(data: tuple[Any, ...]) -> "UserInfo":
        return UserInfo(*data)

    def to_database(self) -> tuple[bool, int]:
        return dataclasses.astuple(self)


def format_timedelta(delta: timedelta) -> str:
    seconds = delta.total_seconds()
    return f"{round(seconds / 3600)} 时 {round(seconds / 60 % 60)} 分"


@command_handler(["morning"], "早上好捏")
async def morning(message: Message):
    now = datetime.now()
    if info := db.get(message.from_id):
        info = UserInfo.from_database(info)
        if info.awake:
            return await message.reply("啊? 都没睡觉, morning 什么? w")
        last = datetime.fromtimestamp(info.last)
        await message.reply(f"早上好 nya~\n你睡了 {format_timedelta(now - last)}呢")
    else:
        await message.reply("早上好 nya~")
    info = UserInfo(True, int(now.timestamp()))
    db[message.from_id] = info.to_database()


@command_handler(["goodnight"], "晚安喵")
async def goodnight(message: Message):
    now = datetime.now()
    if info := db.get(message.from_id):
        info = UserInfo.from_database(info)
        if not info.awake:
            return await message.reply("啊? 都还没醒过, 还睡? w")
        last = datetime.fromtimestamp(info.last)
        await message.reply(f"晚安好梦 mua~\n你醒了 {format_timedelta(now - last)}呢, 忙了一天辛苦捏w")
    else:
        await message.reply("晚安好梦 mua~")
    info = UserInfo(False, int(now.timestamp()))
    db[message.from_id] = info.to_database()
