import contextlib
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (CallbackQuery, ChatActions, ChatMemberStatus, ChatMemberUpdated,
                           ChatType, InlineKeyboardButton, InlineKeyboardMarkup, Message)

from yakusoku import common_config
from yakusoku.archive import avatar_manager, user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.archive.exceptions import ChatDeleted, ChatNotFound
from yakusoku.archive.models import UserData
from yakusoku.filters import CallbackQueryFilter, ManagerFilter, NonAnonymousFilter
from yakusoku.modules import command_handler, dispatcher
from yakusoku.shared.callback import CallbackQueryTaskManager
from yakusoku.shared.lock import SimpleLockManager
from yakusoku.utils import chat, exception

from . import graph
from .manager import (MemberNotEfficientError, NoChoosableWaifuError, WaifuFetchResult,
                      WaifuFetchState, WaifuManager)
from .models import WAIFU_DEFAULT_RARITY, WAIFU_MAX_RARITY, WAIFU_MIN_RARITY
from .registry import Registry

dp = dispatcher()

_manager = WaifuManager()
_registry = Registry(_manager)
_tasks = CallbackQueryTaskManager(dp, "waifu_task/", "任务不见力 QwQ")
_registry_lock = SimpleLockManager()
_graph_lock = SimpleLockManager()


@dataclass(frozen=True)
class MemberWaifuInfo:
    last: datetime
    waifu: int


@command_handler(
    ["waifu"],
    "获取每日老婆 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    NonAnonymousFilter(),
)
async def waifu(message: Message):
    async def _get_waifu(
        message: Message, force: bool = False
    ) -> tuple[WaifuFetchResult, UserData]:
        result = await _manager.fetch_waifu(message.chat.id, message.from_id, force)
        try:
            waifu = await archive_utils.fetch_member(
                message.bot, message.chat.id, result.waifu, True
            )
            return (result, waifu)
        except ChatDeleted:
            if result.state == WaifuFetchState.FORCED:
                await _registry.divorce(message.chat.id, message.from_id)
            return await _get_waifu(message, True)

    await message.answer_chat_action(ChatActions.TYPING)

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
        case WaifuFetchState.FORCED:
            comment = f"你已经结婚啦, 不能抽老婆捏.\n记住你的老婆是 {target}"

    buttons = (
        InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(  # type: ignore
                        text="成立婚事! (仅双方)",
                        callback_data=f"waifu_propose_callback {message.from_id} {waifu.id}",
                    ),
                ]
            ]
        )
        if result.state != WaifuFetchState.FORCED
        else InlineKeyboardMarkup()
    )

    with contextlib.suppress(Exception):
        avatar = await avatar_manager.get_avatar_file(message.bot, waifu.id)
        if avatar:
            return await message.reply_photo(avatar.file_id, comment, reply_markup=buttons)

    await message.reply(comment, reply_markup=buttons)


@command_handler(
    ["waifurs"],
    "修改老婆稀有度 (仅管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    ManagerFilter(),
)
async def waifu_rarity_set(message: Message):
    if (
        not (args := message.get_args())
        or len(args) != 2
        or (rarity := exception.try_or_default(lambda: int(args[1]))) is None
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
    except ChatDeleted and ChatNotFound:
        return await message.reply("呜, 找不到你所提及的用户w")
    data = await _manager.get_waifu_data(message.chat.id, waifu.id)
    data.rarity = rarity
    await _manager.update_waifu_data(data)
    await message.reply(f"成功将 {archive_utils.user_mention_html(waifu)} 的老婆稀有度修改为 {rarity}!")


@command_handler(
    ["waifurg"],
    f"获取老婆稀有度 (仅群聊) (稀有度范围 N, [{WAIFU_MIN_RARITY}, {WAIFU_MAX_RARITY}])",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def waifu_rarity_get(message: Message):
    if len(args := message.text.split()) != 2:
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
        await _registry.divorce(chat, originator.id)
        await query.message.reply(
            f"呜呜呜, {archive_utils.user_mention_html(originator)} "
            f"和 {archive_utils.user_mention_html(target)} 已通过手续离婚了w\n今后的日子, 自己要照顾好自己捏w",
            reply=False,
        )
        with contextlib.suppress(Exception):
            await query.message.delete()
        _registry_lock.unlock_all_unchecked(originator.id, target.id)

    async def cancelled(query: CallbackQuery):
        if query.from_user.id == originator.id:
            await query.answer("取消离婚申请成功捏, 以后要和谐相处哦~")
        else:
            await query.message.reply(
                f"{archive_utils.user_mention_html(originator)} 离婚申请被取消捏, 以后要和谐相处哦~",
                reply=False,
            )
        with contextlib.suppress(Exception):
            await query.message.delete()

    task = _tasks.create_task(
        divorce,
        [
            (lambda query: query.from_user.id != originator.id, "耐心等待对方接受哦w"),  # type: ignore
            (lambda query: query.from_user.id == target.id, "别人的事情不要随便介入哦w"),  # type: ignore
        ],
        expired_after=timedelta(days=1),
    )
    cancellation_task = _tasks.create_cancellation_task(
        task,
        [
            (
                lambda query: query.from_user.id in (originator.id, target.id),  # type: ignore
                "别人的事情不要随便介入哦w",
            )
        ],
        cancelled,
    )
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


@command_handler(
    ["divorce"],
    "提出离婚申请 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    NonAnonymousFilter(),
)
async def divorce(message: Message):
    data = await _manager.get_waifu_data(message.chat.id, message.from_id)
    if not (partner := data.get_partner()):
        return await message.reply("啊? 身为单身狗, 离婚什么???")
    originator = await user_manager.update_from_user(message.from_user)
    target = await user_manager.get_user(partner)
    if not _registry_lock.lock_all(originator.id, target.id):
        return await message.reply("你或者对方正在处理某些事项哦~")
    buttons = create_divorce_task_unchecked(message.chat.id, originator, target)
    await message.reply(
        f"{archive_utils.user_mention_html(originator)} "
        f"向 {archive_utils.user_mention_html(target)} 发起了离婚申请 www",
        reply_markup=buttons,
    )


def create_proposal_task_unchecked(
    chat: int, originator: UserData, target: UserData
) -> InlineKeyboardMarkup:
    async def marry(query: CallbackQuery):
        await _registry.marry(chat, originator.id, target.id)
        await query.message.reply(
            f"恭喜 {archive_utils.user_mention_html(originator)} "
            f"和 {archive_utils.user_mention_html(target)} 已走入婚姻的殿堂捏~\nkdl kdl kdl www",
            reply=False,
        )
        await query.message.reply_sticker(common_config.writing_sticker, reply=False)
        with contextlib.suppress(Exception):
            await query.message.delete()
        _registry_lock.unlock_all_unchecked(originator.id, target.id)

    async def cancelled(query: CallbackQuery):
        if query.from_user.id == target.id:
            await query.message.reply(
                f"呜呜呜, {archive_utils.user_mention_html(originator)} "
                f"被 {archive_utils.user_mention_html(target)} 拒绝了w",
                reply=False,
            )
        else:
            await query.answer("已经帮你取消力~")
        with contextlib.suppress(Exception):
            await query.message.delete()

    task = _tasks.create_task(
        marry,
        [
            (lambda query: query.from_user.id != originator.id, "耐心等待对方接受哦w"),  # type: ignore
            (lambda query: query.from_user.id == target.id, "别人的事情不要随便介入哦w"),  # type: ignore
        ],
        expired_after=timedelta(days=1),
    )
    cancellation_task = _tasks.create_cancellation_task(
        task,
        [
            (
                lambda query: query.from_user.id in (originator.id, target.id),  # type: ignore
                "别人的事情不要随便介入哦w",
            )
        ],
        cancelled,
    )
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


@command_handler(
    ["propose"],
    "提出求婚 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    NonAnonymousFilter(),
)
async def propose(message: Message):
    if (length := len(args := message.text.split())) == 2:
        try:
            target = await archive_utils.parse_member(args[1], message.chat.id, message.bot)
        except ChatDeleted and ChatNotFound:
            return await message.reply("呜, 找不到你所提及的用户w")
    elif length == 1 and message.reply_to_message:
        if message.reply_to_message.sender_chat:
            return await message.reply("呜, 不能跟匿名用户结婚捏w")
        if message.reply_to_message.from_user.is_bot:
            return await message.reply("呜, 不能跟机器人结婚捏w")
        target = await user_manager.update_from_user(message.reply_to_message.from_user)
    else:
        return await message.reply(
            "戳啦, 正确用法为 `/propose <@用户或ID (或回复某个用户的消息)>`", parse_mode="Markdown"
        )

    if message.from_id == target.id:
        return await message.reply("啊? 这是可以选的吗? w")
    if (await _manager.get_waifu_data(message.chat.id, target.id)).get_partner() or (
        await _manager.get_waifu_data(message.chat.id, message.from_id)
    ).get_partner():
        return await message.reply("你或者对方已经结过婚捏, 不能向对方求婚诺w")

    if not _registry_lock.lock_all(message.from_id, target.id):
        return await message.reply("你或者对方正在处理某些事项哦~")

    originator = await user_manager.update_from_user(message.from_user)
    buttons = create_proposal_task_unchecked(message.chat.id, originator, target)
    await message.reply(
        f"{archive_utils.user_mention_html(originator)} "
        f"向 {archive_utils.user_mention_html(target)} 发起了求婚邀请",
        reply_markup=buttons,
    )


@dp.callback_query_handler(CallbackQueryFilter("waifu_propose_callback"))
async def propose_callback(query: CallbackQuery):  # type: ignore
    first_id, second_id = map(int, query.data.split()[1:])
    if query.from_user.id not in (first_id, second_id):
        return await query.answer("别人的事情不要随便介入哦w")
    originator = await user_manager.update_from_user(query.from_user)
    target = await user_manager.get_user(second_id if originator.id == first_id else first_id)
    if not _registry_lock.lock_all(originator.id, target.id):
        return await query.answer("你或者对方正在处理某些事项哦~")
    buttons = create_proposal_task_unchecked(query.message.chat.id, originator, target)
    await query.message.reply(
        f"{chat.get_mention_html(query.from_user)} "
        f"向 {archive_utils.user_mention_html(target)} 发起了求婚邀请",
        reply_markup=buttons,
        reply=False,
    )
    await query.answer()


@command_handler(["waifum"], "允许/禁止 waifu 功能的提及 (默认禁止)", NonAnonymousFilter())
async def mention_global(message: Message):
    config = await _manager.get_waifu_config(message.from_id)
    config.mentionable = not config.mentionable
    await _manager.update_waifu_config(config)
    await message.reply("在所有群别人抽到你做老婆的时候可以通知你哦~" if config.mentionable else "在所有群别人抽老婆的时候不会打扰到你啦~")


@command_handler(
    ["waifug", "waifu_graph"],
    "老婆关系图! (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def waifu_graph(message: Message):
    if not _graph_lock.lock(message.chat.id):
        return await message.reply("呜呜呜, 别骂了, 别骂了, 在画了www")
    reply = await message.reply_sticker(common_config.writing_sticker)
    await message.answer_chat_action(ChatActions.TYPING)
    try:
        datas = await _manager.get_active_waifu_datas(message.chat.id)
        waifu_dict = {data.member: data.waifu for data in datas if data.waifu}
        image = await graph.render(message.bot, waifu_dict, "png")
        await message.reply_photo(image)
    except Exception as ex:
        await message.reply(f"喵呜……渲染失败捏. {ex}")
        traceback.print_exc()
    _graph_lock.unlock(message.chat.id)
    await reply.delete()


@dp.my_chat_member_handler()
@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    if (member := update.new_chat_member).status not in (
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
        ChatMemberStatus.KICKED,
    ):
        return
    if member.user.id == member.bot.id:
        return await _manager.remove_group(update.chat.id)
    with contextlib.suppress(KeyError):
        await _manager.remove_waifu(update.chat.id, member.user.id)
