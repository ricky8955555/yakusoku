import contextlib
from dataclasses import dataclass
from datetime import datetime
from tempfile import TemporaryFile
from typing import Iterable

from aiogram.dispatcher.filters import AdminFilter, ChatTypeFilter
from aiogram.types import ChatMemberUpdated, ChatPhoto, ChatType, Message, User

from ...shared import users
from ...utils import chat, function
from .. import dispatcher
from .factory import WaifuFactory

dp = dispatcher()
DATABASE_NAME = "waifu"


_factory = WaifuFactory()


@dataclass
class MemberWaifuInfo:
    last: datetime
    waifu: int


async def get_user_avatar(user: User) -> ChatPhoto:
    return (await user.bot.get_chat(user.id)).photo


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    commands=["waifu"],
)
async def waifu(message: Message):
    try:
        updated, waifu = await _factory.fetch_waifu(message.chat, message.from_id)
    except IndexError:
        return await message.reply("目前群员信息不足捏, 等我熟悉一下群里环境? w")
    except Exception as ex:
        return await message.reply(f"找不到对象力(悲) www, 错误信息:\n{str(ex)}")

    comment = (
        "每天一老婆哦~ 你今天已经抽过老婆了喵w.\n" if not updated else ""
    ) + f"你今天的老婆是 {waifu.user.get_mention(as_html=True)}"

    with contextlib.suppress(Exception):
        avatar_file = await get_user_avatar(waifu.user)
        with TemporaryFile() as fp:
            await avatar_file.download_small(fp)
            return await message.reply_photo(fp, comment, parse_mode="HTML")

    await message.reply(comment, parse_mode="HTML")


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    AdminFilter(True),
    commands=["waifuf"],
)
async def waifu_forbid(message: Message):
    members = users.get_members(message.chat.id)

    if not (
        members := [
            chat async for chat in await chat.get_mentioned_chats(message) if chat.id in members
        ]
    ):
        return await message.reply("找不到提及的用户")

    for member in members:
        _factory.forbid_waifu(message.chat.id, member.id)

    mentions: Iterable[str] = (member.get_mention(as_html=True) for member in members)
    await message.reply(
        f'已将用户 {" ".join(mentions)} 加入人妻列表',
        parse_mode="HTML",
    )


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    AdminFilter(True),
    commands=["waifua"],
)
async def waifu_allow(message: Message):
    member_ids = users.get_members(message.chat.id)

    if not (
        members := [
            chat async for chat in await chat.get_mentioned_chats(message) if chat.id in member_ids
        ]
    ):
        return await message.reply("找不到提及的用户")

    for member in members:
        _factory.allow_waifu(message.chat.id, member.id)

    mentions: Iterable[str] = (member.get_mention(as_html=True) for member in members)
    await message.reply(
        f'已将用户 {" ".join(mentions)} 移出人妻列表',
        parse_mode="HTML",
    )


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    AdminFilter(True),
    commands=["waifufl"],
)
async def waifu_forbidden_list(message: Message):
    members = [
        await function.try_invoke_or_fallback_async(message.chat.get_member, member)
        for member in _factory.get_forbidden_waifu(message.chat.id)
    ]

    if members:
        await message.reply(
            "这个群的人妻有:\n"
            + "\n".join(
                str(member) if isinstance(member, int) else member.user.full_name
                for member in members
            )
        )
    else:
        await message.reply("这个群没人定下婚事捏")


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    if (member := update.new_chat_member).status == "kicked":
        if member.user.id == member.bot.id:
            _factory.remove_chat(update.chat)
        elif member.user.id in _factory.get_forbidden_waifu(update.chat.id):
            _factory.allow_waifu(update.chat.id, member.user.id)
