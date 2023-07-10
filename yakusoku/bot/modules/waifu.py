import contextlib
import random
from dataclasses import dataclass
from datetime import datetime
from tempfile import TemporaryFile

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (Chat, ChatMember, ChatMemberUpdated, ChatPhoto,
                           ChatType, Message, User)
from sqlitedict import SqliteDict

from .. import database
from ..shared import members
from . import dispatcher

dp = dispatcher()
DATABASE_NAME = "waifu"


@dataclass
class MemberWaifuInfo:
    last: datetime
    waifu: int


async def random_member(group: Chat, sender: User) -> ChatMember:
    members_ = members.get_members(group.id)
    return await group.get_member(
        random.choice([member for member in members_ if member != sender.id])
    )


def get_db(group: Chat) -> SqliteDict:
    return database.get(DATABASE_NAME, str(group.id))


def get_waifu_info(group: Chat, sender: User) -> MemberWaifuInfo | None:
    entry: tuple[int, int] | None = get_db(group).get(  # type: ignore
        sender.id
    )
    return (
        MemberWaifuInfo(
            datetime.fromtimestamp(entry[0]), entry[1]  # type: ignore
        )
        if entry
        else None
    )


def update_waifu_info(
    group: Chat,
    sender: User,
    waifu: MemberWaifuInfo,
) -> None:
    db = get_db(group)
    db[sender.id] = (int(waifu.last.timestamp()), waifu.waifu)


async def fetch_waifu(
    group: Chat,
    sender: User,
) -> tuple[bool, ChatMember]:
    info = get_waifu_info(group, sender)
    now = datetime.now()
    if not info or info.last.date() < now.date():
        member = await random_member(group, sender)
        info = MemberWaifuInfo(now, member.user.id)
        update_waifu_info(group, sender, info)
        return True, member
    else:
        member = await group.get_member(info.waifu)
        return False, member


async def get_user_avatar(user: User) -> ChatPhoto:
    return (await user.bot.get_chat(user.id)).photo


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    commands=["waifu"],
)
async def waifu(message: Message):
    try:
        updated, waifu = await fetch_waifu(message.chat, message.from_user)
    except IndexError:
        return await message.reply("目前群员信息不足捏, 等我熟悉一下群里环境? w")
    except Exception as ex:
        return await message.reply(f"找不到对象力(悲) www, 错误信息:\n{str(ex)}")

    comment = (
        "每天一老婆哦~ 你今天已经抽过老婆了喵w. " if not updated else ""
    ) + f"你今天的老婆是 {waifu.user.get_mention(as_html=True)}"

    with contextlib.suppress(Exception):
        avatar_file = await get_user_avatar(waifu.user)
        with TemporaryFile() as fp:
            await avatar_file.download_small(fp)
            return await message.reply_photo(fp, comment, parse_mode="HTML")

    await message.reply(comment, parse_mode="HTML")


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    if (
        member := update.new_chat_member
    ).status == "kicked" and member.user.id == member.bot.id:
        get_db(update.chat).clear()
