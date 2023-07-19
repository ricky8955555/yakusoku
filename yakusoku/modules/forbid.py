import contextlib
from datetime import timedelta

from aiogram.dispatcher.filters import AdminFilter, ChatTypeFilter
from aiogram.types import ChatMemberStatus, ChatMemberUpdated, ChatType, Message

from yakusoku import database
from yakusoku.modules import command_handler, dispatcher
from yakusoku.utils import chat, function

db: dict[int, int | None] = database.get("forbid", "forbid")
dp = dispatcher()


MAX_BAN_MINUTES = 366 * 24 * 60


@command_handler(
    ["forbidu"],
    "解除进入本群的限制 (仅管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    AdminFilter(),
)
async def forbid_unset(message: Message):
    with contextlib.suppress(KeyError):
        del db[message.chat.id]
    await message.reply("已解除进入本群的限制捏w")


@command_handler(
    ["forbid"],
    "禁止进入本群 (仅管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    AdminFilter(),
)
async def forbid(message: Message):
    time = None
    if (length := len(splited := message.text.split())) > 2 or (
        length == 2 and not (time := function.try_invoke_or_default(lambda: int(splited[1])))
    ):
        return await message.reply(
            "戳啦, 正确用法为 `/forbid [时长 (单位: 分钟) (留空则为永久封禁)]`", parse_mode="Markdown"
        )
    if not time:
        db[message.chat.id] = None
        return await message.reply("设置成功nya~ 进入本群的用户将会被 永久封禁 捏!")
    if time < 0:
        return await message.reply("啊? 时间倒流大法?")
    if time > MAX_BAN_MINUTES:
        return await message.reply("不能封这么长时间捏w")
    db[message.chat.id] = time
    return await message.reply(f"设置成功nya~ 进入本群的用户将会被封禁 {time} 分钟捏!")


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    if (
        not (member := update.new_chat_member).status == ChatMemberStatus.MEMBER
        or update.chat.id not in db
        or (await update.chat.get_member(update.from_user.id)).is_chat_admin()
    ):
        return
    if time := db[update.chat.id]:
        assert time > 0
        await update.bot.send_message(
            update.chat.id,
            f"由于用户 {chat.get_mention_html(member.user)} 违反规定进入本群, 已被封禁 {time} 分钟",
            parse_mode="HTML",
        )
        await update.chat.kick(member.user.id, timedelta(minutes=time))
    else:
        await update.bot.send_message(
            update.chat.id,
            f"由于用户 {chat.get_mention_html(member.user)} 违反规定进入本群, 已被永久封禁",
            parse_mode="HTML",
        )
        await update.chat.kick(member.user.id, timedelta())
