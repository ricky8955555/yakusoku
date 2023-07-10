from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (Chat, ChatMember, ChatMemberUpdated, ChatType,
                           Message, User)

from ..shared import members
from . import dispatcher

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


def is_recordable(user: User):
    return user and user.id > 0 and user.id not in filtered


async def joined(group: Chat, member: ChatMember):
    if is_recordable(member.user):
        members.add_member(group.id, member.user.id)


async def left(group: Chat, member: ChatMember):
    if member.user.id == member.bot.id:
        members.clear_members(group.id)
    else:
        members.remove_member(group.id, member.user.id)


@dp.chat_member_handler()
async def member_update(update: ChatMemberUpdated):
    group, user = update.chat, update.new_chat_member
    if user.status == "member":
        await joined(group, user)
    elif user.status == "kicked":
        await left(group, user)


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def message_received(message: Message):
    if not message.sender_chat and is_recordable(message.from_user):
        members.add_member(message.chat.id, message.from_id)


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    commands=["members"],
)
async def get_members(message: Message):
    async def try_get_member(user_id: int):
        try:
            return await message.chat.get_member(user_id)
        except Exception:
            return user_id

    members_ = [
        await try_get_member(member)
        for member in members.get_members(message.chat.id)
    ]
    await message.reply(
        "当前已记录以下用户信息:\n"
        + "\n".join(
            str(member) if isinstance(member, int) else member.user.full_name
            for member in members_
        ),
        parse_mode="HTML",
    )
