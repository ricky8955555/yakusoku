from aiogram.dispatcher.filters import AdminFilter, ChatTypeFilter
from aiogram.types import Chat, ChatMember, ChatMemberUpdated, ChatType, Message, User

from ..shared import users
from ..utils import function
from . import command_handler, dispatcher

dp = dispatcher()

filtered = [
    777000,
    136817688,
    609517172,
    1031952739,
    1087968824,
    5304501737,
    dp.bot.id,
]


def is_recordable(user: User) -> bool:
    return user and user.id > 0 and user.id not in filtered


async def joined(group: Chat, member: ChatMember) -> None:
    if is_recordable(member.user):
        users.add_member(group.id, member.user.id)
        if member.user.username:
            users.update_user(member.user.username, member.user.id)


async def left(group: Chat, member: ChatMember) -> None:
    if member.user.id == member.bot.id:
        users.delete_members(group.id)
    else:
        users.remove_member(group.id, member.user.id)


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    group, user = update.chat, update.new_chat_member
    if user.status == "member":
        await joined(group, user)
    elif user.status == "kicked":
        await left(group, user)


@dp.message_handler()
async def message_received(message: Message):
    if not message.sender_chat and is_recordable(message.from_user):
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            users.add_member(message.chat.id, message.from_id)
        if message.from_user.username:
            users.update_user(message.from_user.username, message.from_id)


@command_handler(
    ["members"],
    "获取记录成员列表 (仅群聊管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    AdminFilter(),
)
async def get_members(message: Message):
    members = [
        await function.try_invoke_or_fallback_async(message.chat.get_member, member)
        for member in users.get_members(message.chat.id)
    ]
    await message.reply(
        "当前已记录以下成员信息:\n"
        + "\n".join(
            str(member) if isinstance(member, int) else member.user.full_name for member in members
        )
    )
