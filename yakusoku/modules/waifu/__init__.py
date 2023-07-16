import contextlib
from dataclasses import dataclass
from datetime import datetime

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (CallbackQuery, Chat, ChatMemberUpdated, ChatType, InlineKeyboardButton,
                           InlineKeyboardMarkup, Message, User)

from yakusoku.filters import CallbackQueryFilter, ManagerFilter
from yakusoku.modules import command_handler, dispatcher
from yakusoku.shared import user_factory
from yakusoku.utils import chat, function

from . import graph, utils
from .factory import (WAIFU_MAX_RARITY, WAIFU_MIN_RARITY, MemberNotEfficientError,
                      NoChoosableWaifuError, WaifuFactory, WaifuLocalProperty, WaifuState)
from .registry import (InvalidTargetError, MarriageStateError, QueueingError, Registry,
                       TargetUnmatchedError)

dp = dispatcher()

_factory = WaifuFactory()
_registry = Registry(_factory)


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
    try:
        info = _factory.fetch_waifu(message.chat.id, message.from_id)
    except MemberNotEfficientError:
        return await message.reply("目前群员信息不足捏, 等我熟悉一下群里环境? w")
    except NoChoosableWaifuError:
        return await message.reply("你群全成限定了怎么抽? (恼)")
    except Exception as ex:
        await message.reply(f"找不到对象力(悲) www, 错误信息:\n{str(ex)}")
        raise

    waifu = await chat.get_chat(message.bot, info.member)
    mentionable = utils.local_or_global(
        _factory, lambda property: property.mentionable, message.chat.id, waifu.id
    )
    target = waifu.get_mention(as_html=True) if mentionable else waifu.full_name  # type: ignore
    match info.state:
        case WaifuState.NONE:
            comment = f"每天一老婆哦~ 你今天已经抽过老婆了喵w.\n你今天的老婆是 {target}"
        case WaifuState.UPDATED:
            comment = f"你今天的老婆是 {target}"
        case WaifuState.MARRIED:
            comment = f"你已经结婚啦, 不能抽老婆捏.\n记住你的老婆是 {target}"

    buttons = (
        InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(  # type: ignore
                        text="变成限定老婆 (仅管理员)",
                        callback_data=f"waifu_limit_callback {waifu.id}",
                    ),
                    InlineKeyboardButton(  # type: ignore
                        text="成立婚事! (仅双方)",
                        callback_data=f"waifu_propose_callback {message.from_id} {waifu.id}",
                    ),
                ]
            ]
        )
        if info.state != WaifuState.MARRIED
        else InlineKeyboardMarkup()
    )

    with contextlib.suppress(Exception):
        avatar = await user_factory.get_avatar(waifu)
        return await message.reply_photo(avatar, comment, parse_mode="HTML", reply_markup=buttons)

    await message.reply(comment, parse_mode="HTML", reply_markup=buttons)


@command_handler(
    ["waifurs"],
    "修改老婆稀有度 (仅管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    ManagerFilter(),
)
async def waifu_rarity_set(message: Message):
    if not (await message.chat.get_member(message.from_user.id)).is_chat_admin():
        return await message.reply("只有管理员才能修改老婆稀有度嗷!")
    if (
        len(args := message.text.split()) != 3
        or (rarity := function.try_invoke_or_default(lambda: int(args[2]))) is None
        or not WaifuLocalProperty.is_valid_rarity(rarity)
    ):
        return await message.reply(
            f"戳啦, 正确用法为 `/waifurs <@用户> <稀有度> (稀有度范围 N, [{WAIFU_MIN_RARITY}, {WAIFU_MAX_RARITY}])`",
            parse_mode="Markdown",
        )
    try:
        waifu = await utils.get_mentioned_member(message.chat, args[1])
    except AssertionError:
        return await message.reply("呜, 找不到你所提及的用户w")
    _factory.update_waifu_local_property(message.chat.id, waifu.id, rarity=rarity)
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
        waifu = await utils.get_mentioned_member(message.chat, args[1])
    except AssertionError:
        return await message.reply("呜, 找不到你所提及的用户w")
    property = _factory.get_waifu_local_property(message.chat.id, waifu.id)
    await message.reply(
        f"{waifu.get_mention(as_html=True)} 的老婆稀有度为: {property.rarity}", parse_mode="HTML"
    )
    return True


@dp.callback_query_handler(
    CallbackQueryFilter("waifu_limit_callback"),
    ManagerFilter(),
)
async def limit_callback(query: CallbackQuery):
    waifu_id = int(query.data.split()[1])
    _factory.update_waifu_local_property(query.message.chat.id, waifu_id, rarity=WAIFU_MAX_RARITY)
    waifu = await chat.get_chat(query.bot, waifu_id)

    await query.message.reply(
        f"已将用户 {waifu.get_mention(as_html=True)} 变为限定老婆",
        parse_mode="HTML",
    )


async def handle_divorce_request(
    message: Message, originator: Chat | User, removable: bool = False
):
    property = _factory.get_waifu_local_property(message.chat.id, originator.id)
    if not property.married:
        return await message.reply("啊? 身为单身狗, 离婚什么???")
    target = await chat.get_chat(message.bot, property.married)
    try:
        divorced = _registry.request_divorce(message.chat.id, originator.id)
    except QueueingError:
        return await message.reply(
            f"你已经向 {target.get_mention(as_html=True)} 提出了求婚 www, 如果感觉不合适可以取消离婚申请捏 (x",
            parse_mode="HTML",
            reply=not removable,
        )
    if divorced:
        await message.reply(
            f"呜呜呜, {originator.get_mention(as_html=True)} 和 {target.get_mention(as_html=True)} "
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
            f"{originator.get_mention(as_html=True)} 向 {target.get_mention(as_html=True)} "
            "发起了离婚申请 www",
            parse_mode="HTML",
            reply_markup=buttons,
            reply=not removable,
        )


@command_handler(
    ["divorce"],
    "提出离婚申请 (仅群聊)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def request_divorce(message: Message):
    await handle_divorce_request(message, message.from_user or message.sender_chat)


@dp.callback_query_handler(CallbackQueryFilter("waifu_divorce_callback"))
async def divorce_callback(query: CallbackQuery):
    target = int(query.data.split()[1])
    if query.from_user.id != target:
        return
    await handle_divorce_request(query.message, query.from_user, True)


@dp.callback_query_handler(CallbackQueryFilter("waifu_revoke_divorce_request_callback"))
async def revoke_divorce_request_callback(query: CallbackQuery):
    if query.from_user.id not in map(int, query.data.split()[1:]):
        return
    _registry.revoke_divorce_request(query.message.chat.id, query.from_user.id)
    await query.message.reply("取消离婚申请成功捏, 以后要和谐相处哦~", reply=False)
    await query.message.delete()


async def handle_proposal(
    message: Message, originator: Chat | User, target: Chat | User, removable: bool = False
):
    try:
        married = _registry.propose(message.chat.id, originator.id, target.id)
    except InvalidTargetError:
        return await message.reply("啊? 这是可以选的吗? w", reply=not removable)
    except MarriageStateError:
        return await message.reply("你或者对方已经结过婚捏, 不能向对方求婚诺w", reply=not removable)
    except QueueingError:
        proposal = _registry.get_proposal(message.chat.id, originator.id)
        proposal_target = await chat.get_chat(message.bot, proposal)
        return await message.reply(
            f"你已经向 {proposal_target.get_mention(as_html=True)} 提出了求婚捏, 如果感觉不合适可以取消求婚申请捏",
            parse_mode="HTML",
            reply=not removable,
        )
    except TargetUnmatchedError:
        proposal = _registry.get_proposal(message.chat.id, target.id)
        proposal_target = await chat.get_chat(message.bot, proposal)
        return await message.reply(
            f"对方已经向 {proposal_target.get_mention(as_html=True)} 提出了求婚捏, 暂时不能向对方提出求婚申请w",
            parse_mode="HTML",
            reply=not removable,
        )
    if married:
        await message.reply(
            f"恭喜 {originator.get_mention(as_html=True)} 和 {target.get_mention(as_html=True)} "
            "已走入婚姻的殿堂捏~\nkdl kdl kdl www",
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
            f"{originator.get_mention(as_html=True)} 向 {target.get_mention(as_html=True)} 发起了求婚邀请",
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
    if len(args := message.text.split()) != 2:
        return await message.reply("戳啦, 正确用法为 `/propose <@用户>`", parse_mode="Markdown")
    try:
        target = await utils.get_mentioned_member(message.chat, args[1])
    except AssertionError:
        return await message.reply("呜, 找不到你所提及的用户w")
    await handle_proposal(message, message.from_user, target)


@dp.callback_query_handler(CallbackQueryFilter("waifu_propose_callback"))
async def propose_callback(query: CallbackQuery):
    first_id, second_id = map(int, query.data.split()[1:])
    if query.from_user.id == first_id:
        await handle_proposal(
            query.message, query.from_user, await chat.get_chat(query.bot, second_id), True
        )
    elif query.from_user.id == second_id:
        await handle_proposal(
            query.message, query.from_user, await chat.get_chat(query.bot, first_id), True
        )


@dp.callback_query_handler(CallbackQueryFilter("waifu_revoke_proposal_callback"))
async def revoke_proposal_callback(query: CallbackQuery):
    originator_id = int(query.data.split()[1])
    target_id = _registry.get_proposal(query.message.chat.id, originator_id)
    if query.from_user.id not in (originator_id, target_id):
        return
    _registry.revoke_proposal(query.message.chat.id, originator_id)
    if query.from_user.id == originator_id:
        await query.message.reply("取消求婚请求成功捏, 求婚要三思而后行喏~", reply=False)
    else:
        originator = await chat.get_chat(query.bot, originator_id)
        await query.message.reply(
            f"{originator.get_mention(as_html=True)} 被 {query.from_user.get_mention(as_html=True)} "
            "拒绝了捏, 求婚要三思而后行喏~",
            parse_mode="HTML",
            reply=False,
        )
    await query.message.delete()


@command_handler(["waifumg"], "全局允许/禁止 waifu 功能的提及 (默认禁止)")
async def mention_global(message: Message):
    if message.sender_chat:
        return
    global_ = _factory.get_waifu_global_property(message.from_id)
    local = _factory.get_waifu_local_property(message.chat.id, message.from_id)
    if global_.mentionable:
        _factory.update_waifu_global_property(message.from_id, mentionable=False)
        await message.reply(
            "在所有群别人抽老婆的时候不会打扰到你啦~ " + ("" if local.mentionable is None else "(当前群不受全局设置影响)")
        )
    else:
        _factory.update_waifu_global_property(message.from_id, mentionable=True)
        await message.reply(
            "在所有群别人抽到你做老婆的时候可以通知你哦~" + ("" if local.mentionable is None else "(当前群不受全局设置影响)")
        )


@command_handler(["waifuml"], "在当前群允许/禁止 waifu 功能的提及 (默认全局设置)")
async def mention_local(message: Message):
    if message.sender_chat:
        return
    mentionable = utils.local_or_global(
        _factory, lambda property: property.mentionable, message.chat.id, message.from_id
    )
    if mentionable:
        _factory.update_waifu_local_property(message.chat.id, message.from_id, mentionable=False)
        await message.reply("在当前群别人抽老婆的时候不会打扰到你啦~")
    else:
        _factory.update_waifu_local_property(message.chat.id, message.from_id, mentionable=True)
        await message.reply("在当前群别人抽到你做老婆的时候可以通知你哦~")


@command_handler(["waifumc"], "清除 waifu 功能的提及在当前群的局部设置")
async def mention_clear(message: Message):
    if message.sender_chat:
        return
    _factory.update_waifu_local_property(message.chat.id, message.from_id, mentionable=None)
    await message.reply("清除成功了喵w")


@command_handler(["waifug"], "老婆关系图!", run_task=True)
async def waifu_graph(message: Message):
    image = await graph.render_from_cache(_factory.get_waifus(message.chat.id), "png")
    await message.reply_photo(image)


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    if (member := update.new_chat_member).status not in ["left", "kicked"]:
        return
    if member.user.id == member.bot.id:
        _factory.remove_chat(update.chat.id)
    else:
        with contextlib.suppress(KeyError):
            _factory.remove_waifu(update.chat.id, member.user.id)
