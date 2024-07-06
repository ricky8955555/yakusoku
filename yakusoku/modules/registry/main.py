import contextlib
from datetime import timedelta

from aiogram import Bot
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.enums import ChatMemberStatus, ChatType
from aiogram.filters import Command
from aiogram.types import Chat, ChatMemberUpdated, Message, User
from cashews.wrapper import Cache

from yakusoku.archive import group_manager, user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.config import Config
from yakusoku.context import module_manager
from yakusoku.filters import GroupFilter, ManagerFilter, NonAnonymousFilter

router = module_manager.create_router()

cache = Cache()
cache.setup("mem://")


class RegistryConfig(Config):
    auto_update_ttl: timedelta = timedelta(minutes=30)


config = RegistryConfig.load("registry")


async def joined(bot: Bot, group: Chat, member: User) -> None:
    await group_manager.update_group_from_chat(group)
    if member.id != bot.id:
        await user_manager.update_from_user(member)
        await group_manager.add_member(group.id, member.id)


async def left(bot: Bot, group: Chat, member: User) -> None:
    if member.id == bot.id:
        with contextlib.suppress(Exception):
            await group_manager.remove_group(group.id)
    else:
        await group_manager.remove_member(group.id, member.id)


async def permission_check(bot: Bot, update: ChatMemberUpdated) -> None:
    if update.chat.type == ChatType.GROUP:
        await bot.send_message(
            update.chat.id, "我看不到这个群有谁捏, 给我个管理员权限好嘛w, 不然很多功能没法使用唔xwx"
        )
    elif update.new_chat_member.status == ChatMemberStatus.RESTRICTED:
        await bot.send_message(update.chat.id, "坏诶, 怎么被限制了w")
    elif update.new_chat_member.status not in [
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    ]:
        await bot.send_message(
            update.chat.id, "我没法知道这个群有谁会进进出出捏, 给我个管理员权限好嘛w"
        )
    else:
        await bot.send_message(update.chat.id, "好耶!")


@router.my_chat_member
@router.chat_member
async def member_update(update: ChatMemberUpdated, bot: Bot):
    group, member = update.chat, update.new_chat_member
    if member.status == ChatMemberStatus.MEMBER:
        await joined(bot, group, member.user)
    elif member.status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]:
        return await left(bot, group, member.user)
    if member.user.id == bot.id:
        await permission_check(bot, update)
    raise SkipHandler


@router.message(NonAnonymousFilter)
@cache(ttl=config.auto_update_ttl, key="chat:{message.chat.id},user:{message.from_id}")
async def message_received(message: Message):
    assert message.from_user
    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        await group_manager.update_group_from_chat(message.chat)
        await group_manager.add_member(message.chat.id, message.from_user.id)
    else:
        await user_manager.update_from_chat(message.chat)
    await user_manager.update_from_user(message.from_user)
    raise SkipHandler


@router.message(Command("members"), GroupFilter, ManagerFilter)
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
