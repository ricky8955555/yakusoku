from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (Chat, ChatMember, ChatMemberStatus, ChatMemberUpdated, ChatType,
                           ContentType, Message, User)

from yakusoku.filters import ManagerFilter
from yakusoku.modules import command_handler, dispatcher
from yakusoku.shared import user_factory

dp = dispatcher()


filtered = [
    777000,
    136817688,
    609517172,
    1031952739,
    1087968824,
    5304501737,
]


def is_recordable(user: User) -> bool:
    return user and user.id > 0 and not user.is_bot and user.id not in filtered


async def joined(group: Chat, member: ChatMember) -> None:
    if is_recordable(member.user):
        user_factory.add_member(group.id, member.user.id)
        user_factory.update_user(member.user)


async def left(group: Chat, member: ChatMember) -> None:
    if member.user.id == member.bot.id:
        user_factory.clear_members(group.id)
    else:
        user_factory.remove_member(group.id, member.user.id)


@dp.chat_member_handler(run_task=True)
async def member_update(update: ChatMemberUpdated):
    group, user = update.chat, update.new_chat_member
    if user.status == ChatMemberStatus.MEMBER:
        await joined(group, user)
    elif user.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, ChatMemberStatus.KICKED]:
        await left(group, user)


@dp.message_handler(run_task=True, content_types=ContentType.all())
async def message_received(message: Message):
    if not message.sender_chat and is_recordable(message.from_user):
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            user_factory.add_member(message.chat.id, message.from_id)
        user_factory.update_user(message.from_user)


@command_handler(
    ["members"],
    "获取记录成员列表 (仅管理员)",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    ManagerFilter(),
)
async def get_members(message: Message):
    await message.reply(
        "当前已记录以下成员信息:\n"
        + "\n".join(
            (info := user_factory.get_userinfo(member)).name
            or (next(iter(info.usernames)) if info.usernames else str(member))
            for member in user_factory.get_members(message.chat.id)
        )
    )
