import contextlib
from datetime import timedelta

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import (
    Chat,
    ChatMember,
    ChatMemberStatus,
    ChatMemberUpdated,
    ChatType,
    ContentType,
    Message,
)
from cashews.wrapper import Cache

from yakusoku.archive import group_manager, user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.config import Config
from yakusoku.context import module_manager
from yakusoku.filters import ManagerFilter

dp = module_manager.dispatcher()

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
        with contextlib.suppress(Exception):
            await group_manager.remove_group(group.id)
    else:
        await group_manager.remove_member(group.id, member.user.id)


async def permission_check(group: Chat, member: ChatMember) -> None:
    if group.type == ChatType.GROUP:
        await group.bot.send_message(group.id, "我看不到这个群有谁捏, 给我个管理员权限好嘛w, 不然很多功能没法使用唔xwx")
    elif not member.is_chat_admin():
        await group.bot.send_message(group.id, "我没法知道这个群有谁会进进出出捏, 给我个管理员权限好嘛w")
    elif member.status == ChatMemberStatus.RESTRICTED:
        await group.bot.send_message(group.id, "坏诶, 怎么被限制了w")
    else:
        await group.bot.send_message(group.id, "好耶!")


@dp.my_chat_member_handler(run_task=True)
@dp.chat_member_handler(run_task=True)
async def member_update(update: ChatMemberUpdated):
    group, member = update.chat, update.new_chat_member
    if member.status == ChatMemberStatus.MEMBER:
        await joined(group, member)
    elif member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED, ChatMemberStatus.KICKED]:
        return await left(group, member)
    if member.user.id == update.bot.id:
        await permission_check(group, member)


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


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    ManagerFilter(),
    commands=["members"],
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
