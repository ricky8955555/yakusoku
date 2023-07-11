import contextlib
import dataclasses
from dataclasses import dataclass
from datetime import datetime
from io import IOBase
from tempfile import TemporaryFile

from aiogram.dispatcher.filters import AdminFilter, ChatTypeFilter
from aiogram.types import (CallbackQuery, Chat, ChatMemberUpdated, ChatType, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, User)

from ...filters import CallbackQueryFilter
from ...shared import users
from ...utils import chat, function
from .. import command_handler, dispatcher
from .config import Config
from .factory import (WAIFU_MAX_RARITY, WAIFU_MIN_RARITY, MemberNotEfficientError,
                      NoChoosableWaifuError, WaifuFactory, WaifuProperty)

dp = dispatcher()
DATABASE_NAME = "waifu"


_factory = WaifuFactory()
_config = Config.load("bot/waifu")


@dataclass(frozen=True)
class MemberWaifuInfo:
    last: datetime
    waifu: int


async def get_user_avatar(user: User, buffer: IOBase | str) -> IOBase:
    chat = await user.bot.get_chat(user.id)
    avatar = chat.photo
    if _config.original_size:
        return await avatar.download_big(buffer)
    else:
        return await avatar.download_small(buffer)


@command_handler(
    ["waifu"],
    "获取每日老婆 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def waifu(message: Message):
    try:
        updated, waifu = await _factory.fetch_waifu(message.chat, message.from_id)
    except MemberNotEfficientError:
        return await message.reply("目前群员信息不足捏, 等我熟悉一下群里环境? w")
    except NoChoosableWaifuError:
        return await message.reply("你群全成限定了怎么抽? (恼)")
    except Exception as ex:
        await message.reply(f"找不到对象力(悲) www, 错误信息:\n{str(ex)}")
        raise

    comment = (
        "每天一老婆哦~ 你今天已经抽过老婆了喵w.\n" if not updated else ""
    ) + f"你今天的老婆是 {waifu.user.get_mention(as_html=True)}"

    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(  # type: ignore
                    text="变成限定老婆 (仅群聊管理员)",
                    callback_data=f"waifu_limit_callback {message.chat.id} {waifu.user.id}",
                )
            ]
        ]
    )

    with contextlib.suppress(Exception):
        with TemporaryFile() as fp:
            await get_user_avatar(waifu.user, fp)
            return await message.reply_photo(fp, comment, parse_mode="HTML", reply_markup=buttons)

    await message.reply(comment, parse_mode="HTML", reply_markup=buttons)


async def get_mentioned_member(message: Message, username: str) -> Chat:
    assert (
        member := await function.try_invoke_or_default_async(
            lambda: chat.get_chat_from_username(message.bot, username)
        )
    ) and member.id in users.get_members(message.chat.id)
    return member


@command_handler(
    ["waifurs"],
    "修改老婆稀有度 (仅群聊管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    AdminFilter(),
)
async def waifu_rarity_set(message: Message):
    if not (await message.chat.get_member(message.from_user.id)).is_chat_admin():
        return await message.reply("只有群聊管理员才能修改老婆稀有度嗷!")
    if (
        len(args := message.text.split()) != 3
        or (rarity := function.try_invoke_or_default(lambda: int(args[2]))) is None
        or not WaifuProperty.is_valid_rarity(rarity)
    ):
        return await message.reply(
            f"戳啦, 正确用法为 `/waifurs <@用户> <稀有度> (稀有度范围 N, [{WAIFU_MIN_RARITY}, {WAIFU_MAX_RARITY}])`",
            parse_mode="Markdown",
        )
    try:
        waifu = await get_mentioned_member(message, args[1])
    except AssertionError:
        return await message.reply("呜, 找不到你所提及的用户w")
    property = _factory.get_waifu_property(message.chat.id, waifu.id)
    property = dataclasses.replace(property, rarity=rarity)
    _factory.set_waifu_property(message.chat.id, waifu.id, property)
    await message.reply(
        f"成功将 {waifu.get_mention(as_html=True)} 的老婆稀有度修改为 {rarity}!", parse_mode="HTML"
    )


@command_handler(
    ["waifurg"],
    f"获取老婆稀有度 (仅群聊) (稀有度范围 N, [{WAIFU_MIN_RARITY}, {WAIFU_MAX_RARITY}])",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def waifu_rarity_get(message: Message):
    if len(args := message.text.split()) != 2:
        return await message.reply("戳啦, 正确用法为 `/waifurg <@用户>`", parse_mode="Markdown")
    try:
        waifu = await get_mentioned_member(message, args[1])
    except AssertionError:
        return await message.reply("呜, 找不到你所提及的用户w")
    property = _factory.get_waifu_property(message.chat.id, waifu.id)
    await message.reply(
        f"{waifu.get_mention(as_html=True)} 的老婆稀有度为: {property.rarity}", parse_mode="HTML"
    )
    return True


@dp.callback_query_handler(
    CallbackQueryFilter("waifu_limit_callback"),
    AdminFilter(),
)
async def waifu_limit_callback(query: CallbackQuery):
    chat_id, waifu_id = map(int, query.data.split()[1:])
    property = _factory.get_waifu_property(chat_id, waifu_id)
    property = dataclasses.replace(property, rarity=WAIFU_MAX_RARITY)
    _factory.set_waifu_property(chat_id, waifu_id, property)
    waifu = await query.bot.get_chat(waifu_id)

    await query.message.reply(
        f"已将用户 {waifu.get_mention(as_html=True)} 变为限定老婆",
        parse_mode="HTML",
    )


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    if (member := update.new_chat_member).status == "kicked":
        if member.user.id == member.bot.id:
            _factory.remove_chat(update.chat)
