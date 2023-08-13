import contextlib
import traceback
from dataclasses import dataclass
from datetime import datetime

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (CallbackQuery, ChatActions, ChatMemberStatus, ChatMemberUpdated,
                           ChatType, InlineKeyboardButton, InlineKeyboardMarkup, Message)
from sqlalchemy.exc import NoResultFound

from yakusoku import common_config
from yakusoku.archive import avatar_manager, user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.archive.exceptions import ChatDeleted
from yakusoku.archive.models import UserData
from yakusoku.filters import CallbackQueryFilter, ManagerFilter, NonAnonymousFilter
from yakusoku.modules import command_handler, dispatcher
from yakusoku.utils import chat, exception

from . import graph
from .manager import (MemberNotEfficientError, NoChoosableWaifuError, WaifuFetchResult,
                      WaifuFetchState, WaifuManager)
from .models import WAIFU_MAX_RARITY, WAIFU_MIN_RARITY
from .registry import (InvalidTargetError, MarriageStateError, QueueingError, Registry,
                       TargetUnmatchedError)

dp = dispatcher()

_manager = WaifuManager()
_registry = Registry(_manager)


@dataclass(frozen=True)
class MemberWaifuInfo:
    last: datetime
    waifu: int


@command_handler(
    ["waifu"],
    "获取每日老婆 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def waifu(message: Message):
    async def _get_waifu(
        message: Message, force: bool = False
    ) -> tuple[WaifuFetchResult, UserData]:
        result = await _manager.fetch_waifu(message.chat.id, message.from_id, force)
        try:
            waifu = await archive_utils.fetch_member(message.bot, message.chat.id, result.waifu)
            return (result, waifu)
        except ChatDeleted:
            if result.state == WaifuFetchState.FORCED:
                await _registry.divorce(message.chat.id, message.from_id)
            return await _get_waifu(message, True)

    if message.sender_chat:
        return await message.reply("暂不支持匿名身份抽老婆捏w")

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
        if result.state != WaifuFetchState.FORCED and not message.sender_chat
        else InlineKeyboardMarkup()
    )

    with contextlib.suppress(Exception):
        avatar = await avatar_manager.get_avatar_file(message.bot, waifu.id)
        if avatar:
            return await message.reply_photo(
                avatar.file_id, comment, parse_mode="HTML", reply_markup=buttons
            )

    await message.reply(comment, parse_mode="HTML", reply_markup=buttons)


@command_handler(
    ["waifurs"],
    "修改老婆稀有度 (仅管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    ManagerFilter(),
)
async def waifu_rarity_set(message: Message):
    if (
        len(args := message.text.split()) != 3
        or (rarity := exception.try_invoke_or_default(lambda: int(args[2]))) is None
        or not (WAIFU_MIN_RARITY < rarity < WAIFU_MAX_RARITY)
    ):
        return await message.reply(
            f"戳啦, 正确用法为 `/waifurs <@用户> <稀有度> (稀有度范围 N, [{WAIFU_MIN_RARITY}, {WAIFU_MAX_RARITY}])`",
            parse_mode="Markdown",
        )
    try:
        waifu = await user_manager.get_user_from_username(args[1].lstrip("@"))
    except NoResultFound:
        return await message.reply("呜, 找不到你所提及的用户w")
    data = await _manager.get_waifu_data(message.chat.id, waifu.id)
    data.rarity = rarity
    await _manager.update_waifu_data(data)
    await message.reply(
        f"成功将 {archive_utils.user_mention_html(waifu)} 的老婆稀有度修改为 {rarity}!", parse_mode="HTML"
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
        waifu = await user_manager.get_user_from_username(args[1].lstrip("@"))
    except AssertionError:
        return await message.reply("呜, 找不到你所提及的用户w")
    data = await _manager.get_waifu_data(message.chat.id, waifu.id)
    await message.reply(
        f"{archive_utils.user_mention_html(waifu)} 的老婆稀有度为: {data.rarity}", parse_mode="HTML"
    )
    return True


async def handle_divorce_request(message: Message, originator: UserData, removable: bool = False):
    data = await _manager.get_waifu_data(message.chat.id, originator.id)
    if not data.forced:
        return await message.reply("啊? 身为单身狗, 离婚什么???")
    assert data.waifu, "no waifu when forced is true."
    target = await user_manager.get_user(data.waifu)
    try:
        divorced = await _registry.request_divorce(message.chat.id, originator.id)
    except QueueingError:
        return await message.reply(
            f"你已经向 {archive_utils.user_mention_html(target)} 提出了求婚 www, 如果感觉不合适可以取消离婚申请捏 (x",
            parse_mode="HTML",
            reply=not removable,
        )
    if divorced:
        await message.reply(
            f"呜呜呜, {archive_utils.user_mention_html(originator)} "
            f"和 {archive_utils.user_mention_html(target)} "
            "已通过手续离婚了w\n今后的日子, 自己要照顾好自己捏w",
            parse_mode="HTML",
            reply=not removable,
        )
        if removable:
            await message.delete()
    else:
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(  # type: ignore
                        text="接受离婚 www (仅被请求者)",
                        callback_data=f"waifu_divorce_callback {target.id}",
                    ),
                    InlineKeyboardButton(  # type: ignore
                        text="口头挖路! / 取消请求 (仅双方)",
                        callback_data=(
                            f"waifu_revoke_divorce_request_callback {originator.id} {target.id}"
                        ),
                    ),
                ]
            ]
        )
        await message.reply(
            f"{archive_utils.user_mention_html(originator)} "
            f"向 {archive_utils.user_mention_html(target)} "
            "发起了离婚申请 www",
            parse_mode="HTML",
            reply_markup=buttons,
            reply=not removable,
        )


@command_handler(
    ["divorce"],
    "提出离婚申请 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    NonAnonymousFilter(),
)
async def request_divorce(message: Message):
    await handle_divorce_request(message, await user_manager.get_user(message.from_id))


@dp.callback_query_handler(CallbackQueryFilter("waifu_divorce_callback"))
async def divorce_callback(query: CallbackQuery):
    target = int(query.data.split()[1])
    if query.from_user.id != target:
        await query.answer("别人的家事不要瞎掺和w")
        return
    await query.answer()
    await handle_divorce_request(
        query.message, await user_manager.get_user(query.from_user.id), True
    )


@dp.callback_query_handler(CallbackQueryFilter("waifu_revoke_divorce_request_callback"))
async def revoke_divorce_request_callback(query: CallbackQuery):
    if query.from_user.id not in map(int, query.data.split()[1:]):
        await query.answer("别人的家事不要瞎掺和w")
        return
    await query.answer()
    await _registry.revoke_divorce_request(query.message.chat.id, query.from_user.id)
    await query.message.reply("取消离婚申请成功捏, 以后要和谐相处哦~", reply=False)
    await query.message.delete()


async def handle_proposal(
    message: Message, originator: UserData, target: UserData, removable: bool = False
):
    try:
        married = await _registry.propose(message.chat.id, originator.id, target.id)
    except InvalidTargetError:
        return await message.reply("啊? 这是可以选的吗? w", reply=not removable)
    except MarriageStateError:
        return await message.reply("你或者对方已经结过婚捏, 不能向对方求婚诺w", reply=not removable)
    except QueueingError:
        proposal = _registry.get_proposal(message.chat.id, originator.id)
        target = await user_manager.get_user(proposal)
        return await message.reply(
            f"你已经向 {archive_utils.user_mention_html(target)} 提出了求婚捏, 如果感觉不合适可以取消求婚申请捏",
            parse_mode="HTML",
            reply=not removable,
        )
    except TargetUnmatchedError:
        proposal = _registry.get_proposal(message.chat.id, target.id)
        target = await user_manager.get_user(proposal)
        return await message.reply(
            f"对方已经向 {archive_utils.user_mention_html(target)} 提出了求婚捏, 暂时不能向对方提出求婚申请w",
            parse_mode="HTML",
            reply=not removable,
        )
    if married:
        await message.reply(
            f"恭喜 {archive_utils.user_mention_html(originator)} "
            f"和 {archive_utils.user_mention_html(target)} "
            "已走入婚姻的殿堂捏~\nkdl kdl kdl www",
            parse_mode="HTML",
            reply=not removable,
        )
        await message.reply_sticker(common_config.writing_sticker, reply=False)
        if removable:
            await message.delete()
    else:
        buttons = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(  # type: ignore
                        text="接受求婚! (仅被请求者)",
                        callback_data=f"waifu_propose_callback {originator.id} {target.id}",
                    ),
                    InlineKeyboardButton(  # type: ignore
                        text="口头挖路! / 取消请求 (仅双方)",
                        callback_data=f"waifu_revoke_proposal_callback {originator.id}",
                    ),
                ]
            ]
        )
        await message.reply(
            f"{archive_utils.user_mention_html(originator)} "
            f"向 {archive_utils.user_mention_html(target)} 发起了求婚邀请",
            parse_mode="HTML",
            reply_markup=buttons,
            reply=not removable,
        )


@command_handler(
    ["propose"],
    "提出求婚 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def propose(message: Message):
    if message.sender_chat:
        return await message.reply("暂不支持匿名身份结婚捏w")

    if (length := len(args := message.text.split())) == 2:
        try:
            target = await user_manager.get_user_from_username(args[1].lstrip("@"))
        except AssertionError:
            return await message.reply("呜, 找不到你所提及的用户w")
    elif length == 1 and message.reply_to_message:
        if message.reply_to_message.sender_chat:
            return await message.reply("呜, 不能跟匿名用户主动结婚捏w")
        if message.reply_to_message.from_user.is_bot:
            return await message.reply("呜, 不能跟机器人结婚捏w")
        target = await user_manager.get_user(message.reply_to_message.from_id)
    else:
        return await message.reply("戳啦, 正确用法为 `/propose <@用户 (或回复某个用户的消息)>`", parse_mode="Markdown")
    await handle_proposal(message, await user_manager.get_user(message.from_id), target)


@dp.callback_query_handler(CallbackQueryFilter("waifu_propose_callback"))
async def propose_callback(query: CallbackQuery):
    first_id, second_id = map(int, query.data.split()[1:])
    if query.from_user.id == first_id:
        await handle_proposal(
            query.message,
            await user_manager.get_user(query.from_user.id),
            await user_manager.get_user(second_id),
            True,
        )
    elif query.from_user.id == second_id:
        await handle_proposal(
            query.message,
            await user_manager.get_user(query.from_user.id),
            await user_manager.get_user(first_id),
            True,
        )
    else:
        await query.answer("别人的事情不要随便介入哦w")
    await query.answer()


@dp.callback_query_handler(CallbackQueryFilter("waifu_revoke_proposal_callback"))
async def revoke_proposal_callback(query: CallbackQuery):
    originator_id = int(query.data.split()[1])
    target_id = _registry.get_proposal(query.message.chat.id, originator_id)
    if query.from_user.id not in (originator_id, target_id):
        await query.answer("别人的事情不要随便介入哦w")
        return
    await query.answer()
    _registry.revoke_proposal(query.message.chat.id, originator_id)
    if query.from_user.id == originator_id:
        await query.message.reply("取消求婚请求成功捏, 求婚要三思而后行喏~", reply=False)
    else:
        originator = await user_manager.get_user(originator_id)
        await query.message.reply(
            f"{archive_utils.user_mention_html(originator)} "
            f"被 {chat.get_mention_html(query.from_user)} "
            "拒绝了捏, 求婚要三思而后行喏~",
            parse_mode="HTML",
            reply=False,
        )
    await query.message.delete()


@command_handler(["waifum"], "允许/禁止 waifu 功能的提及 (默认禁止)", NonAnonymousFilter())
async def mention_global(message: Message):
    config = await _manager.get_waifu_config(message.from_id)
    config.mentionable = not config.mentionable
    await _manager.update_waifu_config(config)
    await message.reply("在所有群别人抽老婆的时候不会打扰到你啦~" if config.mentionable else "在所有群别人抽到你做老婆的时候可以通知你哦~")


@command_handler(
    ["waifug", "waifu_graph"],
    "老婆关系图! (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def waifu_graph(message: Message):
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
    await reply.delete()


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    if (member := update.new_chat_member).status not in [
        ChatMemberStatus.LEFT,
        ChatMemberStatus.BANNED,
        ChatMemberStatus.KICKED,
    ]:
        return
    if member.user.id == member.bot.id:
        await _manager.remove_group(update.chat.id)
    else:
        with contextlib.suppress(KeyError):
            await _manager.remove_waifu(update.chat.id, member.user.id)
