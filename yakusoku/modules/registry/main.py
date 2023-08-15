from datetime import timedelta

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (Chat, ChatMember, ChatMemberStatus, ChatMemberUpdated, ChatType,
                           ContentType, Message)
from cashews.wrapper import Cache

from yakusoku.archive import group_manager, user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.config import Config
from yakusoku.filters import ManagerFilter
from yakusoku.modules import command_handler, dispatcher

dp = dispatcher()

cache = Cache()
cache.setup("mem://")


class RegistryConfig(Config):
    auto_update_ttl: timedelta = timedelta(minutes=30)


config = RegistryConfig.load("registry")


async def joined(group: Chat, member: ChatMember) -> None:
    await group_manager.update_group_from_chat(group)
    if member.user.id != member.bot.id:
        await user_manager.update_from_user(member.user)
        await group_manager.add_member(group.id, member.user.id)


async def left(group: Chat, member: ChatMember) -> None:
    if member.user.id == member.bot.id:
        await group_manager.remove_group(group.id)
    else:
        await group_manager.remove_member(group.id, member.user.id)


@dp.my_chat_member_handler(run_task=True)
@dp.chat_member_handler(run_task=True)
async def member_update(update: ChatMemberUpdated):
    group, user = update.chat, update.new_chat_member
    if user.status == ChatMemberStatus.MEMBER:
        await joined(group, user)
    elif user.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, ChatMemberStatus.KICKED]:
        await left(group, user)


@dp.message_handler(run_task=True, content_types=ContentType.all())
@cache(ttl=config.auto_update_ttl, key="chat:{message.chat.id},user:{message.from_id}")
async def message_received(message: Message):
    if not message.sender_chat:
        if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
            await group_manager.update_group_from_chat(message.chat)
            await group_manager.add_member(message.chat.id, message.from_id)
        else:
            await user_manager.update_from_chat(message.chat)
        await user_manager.update_from_user(message.from_user)


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
            [
                member.name or (member.usernames[0] if member.usernames else str(member.id))
                async for member in archive_utils.get_members(message.chat.id)
            ]
        )
    )