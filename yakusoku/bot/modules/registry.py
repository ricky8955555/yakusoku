from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (Chat, ChatMember, ChatMemberUpdated, ChatType,
                           Message)

from ..shared import members
from . import dispatcher

dp = dispatcher()


async def joined(group: Chat, member: ChatMember):
    members.add_member_id(group.id, member.user.id)


async def left(group: Chat, member: ChatMember):
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
    if message.from_id:
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
