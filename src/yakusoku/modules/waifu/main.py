import contextlib
import html
import time
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.enums import ChatAction, ChatMemberStatus
from aiogram.filters import Command, CommandObject
from aiogram.filters.callback_data import CallbackData, CallbackQueryFilter
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from yakusoku.archive import avatar_manager, user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.archive.exceptions import ChatDeleted, ChatNotFound
from yakusoku.archive.models import UserData
from yakusoku.context import common_config, module_manager, sql
from yakusoku.filters import GroupFilter, ManagerFilter, NonAnonymousFilter
from yakusoku.utils.callback import CallbackQueryTaskManager
from yakusoku.utils.lock import SimpleLockManager
from yakusoku.utils import chat, exception

from . import graph
from .manager import (
    MemberNotEfficientError,
    NoChoosableWaifuError,
    WaifuFetchResult,
    WaifuFetchState,
    WaifuManager,
)
from .models import WAIFU_DEFAULT_RARITY, WAIFU_MAX_RARITY, WAIFU_MIN_RARITY
from .registry import Registry

router = module_manager.create_router()

_manager = WaifuManager(sql)
_registry = Registry(_manager)
_tasks = CallbackQueryTaskManager(router, "waifu_task/", "任务不见力 QwQ")
_registry_lock = SimpleLockManager()
_graph_lock = SimpleLockManager()


@dataclass(frozen=True)
class MemberWaifuInfo:
    last: datetime
    waifu: int


class Propose(CallbackData, prefix="waifu_propose"):
    first: int
    second: int


@router.message(Command("waifu"), GroupFilter, NonAnonymousFilter)
async def waifu(message: Message, bot: Bot):
    assert message.from_user and message.chat
    user_id = message.from_user.id

    async def _get_waifu(
        message: Message, force: bool = False
    ) -> tuple[WaifuFetchResult, UserData]:
        result = await _manager.fetch_waifu(message.chat.id, user_id, force)
        try:
            waifu = await archive_utils.fetch_member(bot, message.chat.id, result.waifu, True)
            return (result, waifu)
        except ChatDeleted:
            if result.state == WaifuFetchState.RESTRICTED:
                await _registry.divorce(message.chat.id, user_id)
            return await _get_waifu(message, True)

    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    try:
        result, waifu = await _get_waifu(message)
    except MemberNotEfficientError:
        return await message.reply("目前群员信息不足捏, 等我熟悉一下群里环境? w")
    except NoChoosableWaifuError:
        return await message.reply("你群全成限定了怎么抽? (恼)")
    except Exception as ex:
        await message.reply(f"找不到对象力(悲) www, 错误信息:\n{str(ex)}")
        raise

    config = await _manager.get_waifu_config(waifu.id)
    target = archive_utils.user_mention_html(waifu) if config.mentionable else waifu.name

    match result.state:
        case WaifuFetchState.NONE:
            comment = f"每天一老婆哦~ 你今天已经抽过老婆了喵w.\n你今天的老婆是 {target}"
        case WaifuFetchState.UPDATED:
            comment = f"你今天的老婆是 {target}"
        case WaifuFetchState.RESTRICTED:
            comment = f"你已经结婚啦, 不能抽老婆捏.\n记住你的老婆是 {target}"

    buttons = (
        InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="成立婚事! (仅双方)",
                        callback_data=Propose(first=user_id, second=waifu.id).pack(),
                    )
                ]
            ]
        )
        if result.state != WaifuFetchState.RESTRICTED
        else None
    )

    with contextlib.suppress(Exception):
        avatar = await avatar_manager.get_avatar_file(bot, waifu.id)
        if avatar:
            return await message.reply_photo(avatar.file_id, comment, reply_markup=buttons)

    await message.reply(comment, reply_markup=buttons)


@router.message(Command("waifurs"), GroupFilter, ManagerFilter)
async def waifu_rarity_set(message: Message, command: CommandObject):
    if (
        not (args := command.args)
        or len(args := args.split()) != 2
        or (rarity := exception.try_or_default(lambda: int(args[1]))) is None  # type: ignore
        or not (WAIFU_MIN_RARITY <= rarity <= WAIFU_MAX_RARITY)
    ):
        return await message.reply(
            "戳啦, 正确用法为 `/waifurs <@用户或ID> <稀有度> "
            f"(稀有度范围 N, [{WAIFU_MIN_RARITY}, {WAIFU_MAX_RARITY}], 默认值为 {WAIFU_DEFAULT_RARITY})`",
            parse_mode="Markdown",
        )
    try:
        waifu = await archive_utils.parse_member(
            args[0].removeprefix("@"), message.chat.id, message.bot
        )
    except (ChatDeleted, ChatNotFound):
        return await message.reply("呜, 找不到你所提及的用户w")
    data = await _manager.get_waifu_data(message.chat.id, waifu.id)
    data.rarity = rarity
    await _manager.update_waifu_data(data)
    await message.reply(
        f"成功将 {archive_utils.user_mention_html(waifu)} 的老婆稀有度修改为 {rarity}!"
    )


@router.message(Command("waifurg"), GroupFilter)
async def waifu_rarity_get(message: Message):
    if not message.text or len(args := message.text.split()) != 2:
        return await message.reply("戳啦, 正确用法为 `/waifurg <@用户或ID>`", parse_mode="Markdown")
    try:
        waifu = await archive_utils.parse_member(
            args[1].removeprefix("@"), message.chat.id, message.bot
        )
    except AssertionError:
        return await message.reply("呜, 找不到你所提及的用户w")
    data = await _manager.get_waifu_data(message.chat.id, waifu.id)
    await message.reply(f"{archive_utils.user_mention_html(waifu)} 的老婆稀有度为: {data.rarity}")


def create_divorce_task_unchecked(
    chat: int, originator: UserData, target: UserData
) -> InlineKeyboardMarkup:
    async def divorce(query: CallbackQuery):
        if not isinstance(query.message, Message):
            return await query.answer("消息太远古了, 我不是考古学家w")
        if query.from_user.id == originator.id:
            await query.answer("耐心等待对方接受哦w")
            return False
        if query.from_user.id != target.id:
            await query.answer("别人的事情不要随便介入哦w")
            return False
        await _registry.divorce(chat, originator.id)
        await query.message.reply(
            f"呜呜呜, {archive_utils.user_mention_html(originator)} "
            f"和 {archive_utils.user_mention_html(target)} 已通过手续离婚了w\n今后的日子, 自己要照顾好自己捏w",
            reply=False,
        )
        with contextlib.suppress(Exception):
            await query.message.delete()

    async def cancelled(query: CallbackQuery):
        if not isinstance(query.message, Message):
            return await query.answer("消息太远古了, 我不是考古学家w")
        if query.from_user.id == originator.id:
            await query.answer("取消离婚申请成功捏, 以后要和谐相处哦~")
        elif query.from_user.id == target.id:
            await query.message.reply(
                f"{archive_utils.user_mention_html(originator)} 离婚申请被取消捏, 以后要和谐相处哦~",
                reply=False,
            )
        else:
            await query.answer("别人的事情不要随便介入哦w")
            return False
        with contextlib.suppress(Exception):
            await query.message.delete()

    async def disposed():
        _registry_lock.unlock_all_unchecked((chat, originator.id), (chat, target.id))

    task = _tasks.create_task(divorce, expired_after=timedelta(days=1), disposed=disposed)
    cancellation_task = _tasks.create_cancellation_task(task, cancelled)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(  # type: ignore
                    text="接受离婚 www (仅被请求者)",
                    callback_data=task.callback_data,
                ),
                InlineKeyboardButton(  # type: ignore
                    text="口头挖路! / 取消请求 (仅双方)",
                    callback_data=cancellation_task.callback_data,
                ),
            ]
        ]
    )


@router.message(Command("divorce"), GroupFilter, NonAnonymousFilter)
async def divorce(message: Message):
    assert message.from_user
    user_id = message.from_user.id
    data = await _manager.get_waifu_data(message.chat.id, user_id)
    if not (partner := data.get_partner()):
        return await message.reply("啊? 身为单身狗, 离婚什么???")
    originator = await user_manager.get_user(user_id)
    target = await user_manager.get_user(partner)
    if not _registry_lock.lock_all((message.chat.id, originator.id), (message.chat.id, target.id)):
        return await message.reply("你或者对方正在处理某些事项哦~")
    buttons = create_divorce_task_unchecked(message.chat.id, originator, target)
    await message.reply(
        f"你向 {archive_utils.user_mention_html(target)} 发起了离婚申请 www",
        reply_markup=buttons,
    )


def create_proposal_task_unchecked(
    chat: int, originator: UserData, target: UserData
) -> InlineKeyboardMarkup:
    async def marry(query: CallbackQuery):
        if not isinstance(query.message, Message):
            return await query.answer("消息太远古了, 我不是考古学家w")
        if query.from_user.id == originator.id:
            await query.answer("耐心等待对方接受哦w")
            return False
        if query.from_user.id != target.id:
            await query.answer("别人的事情不要随便介入哦w")
            return False
        await _registry.marry(chat, originator.id, target.id)
        await query.message.reply(
            f"恭喜 {archive_utils.user_mention_html(originator)} "
            f"和 {archive_utils.user_mention_html(target)} 已走入婚姻的殿堂捏~\nkdl kdl kdl www",
            reply=False,
        )
        await query.message.reply_sticker(common_config.writing_sticker, reply=False)
        with contextlib.suppress(Exception):
            await query.message.delete()

    async def cancelled(query: CallbackQuery):
        if not isinstance(query.message, Message):
            return await query.answer("消息太远古了, 我不是考古学家w")
        if query.from_user.id == target.id:
            await query.message.reply(
                f"呜呜呜, {archive_utils.user_mention_html(originator)} "
                f"被 {archive_utils.user_mention_html(target)} 拒绝了w",
                reply=False,
            )
        elif query.from_user.id == originator.id:
            await query.answer("已经帮你取消力~")
        else:
            await query.answer("别人的事情不要随便介入哦w")
            return False
        with contextlib.suppress(Exception):
            await query.message.delete()

    async def disposed():
        _registry_lock.unlock_all_unchecked((chat, originator.id), (chat, target.id))

    task = _tasks.create_task(marry, expired_after=timedelta(days=1), disposed=disposed)
    cancellation_task = _tasks.create_cancellation_task(task, cancelled)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(  # type: ignore
                    text="接受求婚! (仅被请求者)",
                    callback_data=task.callback_data,
                ),
                InlineKeyboardButton(  # type: ignore
                    text="口头挖路! / 取消请求 (仅双方)",
                    callback_data=cancellation_task.callback_data,
                ),
            ]
        ]
    )


@router.message(Command("propose"), GroupFilter, NonAnonymousFilter)
async def propose(message: Message):
    assert message.from_user
    user_id = message.from_user.id

    args = message.text.split() if message.text else []
    if (length := len(args)) == 2:
        try:
            target = await archive_utils.parse_member(args[1], message.chat.id, message.bot)
        except (ChatDeleted, ChatNotFound):
            return await message.reply("呜, 找不到你所提及的用户w")
    elif length == 1 and message.reply_to_message:
        if message.reply_to_message.sender_chat or not message.reply_to_message.from_user:
            return await message.reply("呜, 不能跟匿名用户结婚捏w")
        if message.reply_to_message.from_user.is_bot:
            return await message.reply("呜, 不能跟机器人结婚捏w")
        target = await user_manager.get_user(message.reply_to_message.from_user.id)
    else:
        return await message.reply(
            "戳啦, 正确用法为 `/propose <@用户或ID (或回复某个用户的消息)>`", parse_mode="Markdown"
        )

    if user_id == target.id:
        return await message.reply("啊? 这是可以选的吗? w")
    if (await _manager.get_waifu_data(message.chat.id, target.id)).get_partner() or (
        await _manager.get_waifu_data(message.chat.id, user_id)
    ).get_partner():
        return await message.reply("你或者对方已经结过婚捏, 不能向对方求婚诺w")

    if not _registry_lock.lock_all((message.chat.id, user_id), (message.chat.id, target.id)):
        return await message.reply("你或者对方正在处理某些事项哦~")

    originator = await user_manager.get_user(user_id)
    buttons = create_proposal_task_unchecked(message.chat.id, originator, target)
    await message.reply(
        f"你向 {archive_utils.user_mention_html(target)} 发起了求婚邀请",
        reply_markup=buttons,
    )


@router.callback_query(CallbackQueryFilter(callback_data=Propose))
async def propose_callback(query: CallbackQuery, callback_data: Propose):  # type: ignore
    if not isinstance(query.message, Message):
        return await query.answer("消息太远古了, 我不是考古学家w")
    first_id, second_id = callback_data.first, callback_data.second
    if query.from_user.id not in [first_id, second_id]:
        return await query.answer("别人的事情不要随便介入哦w")
    originator = await user_manager.get_user(query.from_user.id)
    target = await user_manager.get_user(second_id if originator.id == first_id else first_id)
    if (await _manager.get_waifu_data(query.message.chat.id, target.id)).get_partner() or (
        await _manager.get_waifu_data(query.message.chat.id, originator.id)
    ).get_partner():
        return await query.answer("你或者对方已经结过婚捏, 不能向对方求婚诺w")
    if not _registry_lock.lock_all(
        (query.message.chat.id, originator.id), (query.message.chat.id, target.id)
    ):
        return await query.answer("你或者对方正在处理某些事项哦~")
    buttons = create_proposal_task_unchecked(query.message.chat.id, originator, target)
    await query.message.reply(
        f"{chat.mention_html(query.from_user)} "
        f"向 {archive_utils.user_mention_html(target)} 发起了求婚邀请",
        reply_markup=buttons,
        reply=False,
    )
    await query.answer()


@router.message(Command("waifum"), NonAnonymousFilter)
async def mention_global(message: Message):
    assert message.from_user
    config = await _manager.get_waifu_config(message.from_user.id)
    config.mentionable = not config.mentionable
    await _manager.update_waifu_config(config)
    await message.reply(
        "在所有群别人抽到你做老婆的时候可以通知你哦~"
        if config.mentionable
        else "在所有群别人抽老婆的时候不会打扰到你啦~"
    )


@router.message(Command("waifug", "waifu_graph"), GroupFilter)
async def waifu_graph(message: Message, bot: Bot):
    assert message.chat
    if not _graph_lock.lock(message.chat.id):
        return await message.reply("呜呜呜, 别骂了, 别骂了, 在画了www")
    reply = await message.reply_sticker(common_config.writing_sticker)
    await bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    try:
        datas = await _manager.get_active_waifu_datas(message.chat.id)
        waifu_dict = {data.member: data.waifu for data in datas if data.waifu}
        image = await graph.render(bot, waifu_dict, "png")
        file = BufferedInputFile(image, f"waifug-{message.chat.id}-{time.time()}.png")
        await message.reply_photo(file)
    except Exception as ex:
        await message.reply(f"喵呜……渲染失败捏. {html.escape(str(ex))}")
        traceback.print_exc()
    _graph_lock.unlock(message.chat.id)
    await reply.delete()


@router.my_chat_member
@router.chat_member
async def member_update(update: ChatMemberUpdated, bot: Bot):
    if (member := update.new_chat_member).status not in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.KICKED,
    ):
        return
    if member.user.id == bot.id:
        with contextlib.suppress(Exception):
            return await _manager.remove_group(update.chat.id)
    with contextlib.suppress(KeyError):
        await _manager.remove_waifu(update.chat.id, member.user.id)
    raise SkipHandler
