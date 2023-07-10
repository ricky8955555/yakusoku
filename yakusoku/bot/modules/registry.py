from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (Chat, ChatMember, ChatMemberUpdated, ChatType,
                           Message)

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


async def joined(group: Chat, member: ChatMember):
    if member.user.id not in filtered:
        members.add_member_id(group.id, member.user.id)


async def left(group: Chat, member: ChatMember):
    if member.user.id == member.bot.id:
        members.clear_members(group.id)
    else:
        members.remove_member_id(group.id, member.user.id)


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
    if (
        not message.sender_chat
        and message.from_id
        and message.from_id not in filtered
    ):
        members.add_member_id(message.chat.id, message.from_id)


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    commands=["members"],
)
async def get_members(message: Message):
    members_ = await members.get_members(message.chat)
    await message.reply(
        "当前已记录以下用户信息:\n"
        + "\n".join(
            member.user.get_mention(as_html=True) for member in members_
        ),
        parse_mode="HTML",
    )
