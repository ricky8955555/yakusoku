import contextlib
from typing import AsyncIterable

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils import markdown
from sqlalchemy.exc import NoResultFound

from yakusoku.archive import group_manager, user_manager
from yakusoku.archive.exceptions import ChatDeleted, ChatNotFound
from yakusoku.archive.models import GroupData, UserData
from yakusoku.utils import exception


async def get_members(group: int) -> AsyncIterable[UserData]:
    data = await group_manager.get_group(group)
    for member in data.members:
        yield await user_manager.get_user(member)


async def get_user_members(group: int) -> AsyncIterable[UserData]:
    return (member async for member in get_members(group) if not member.is_bot)


def user_url(user: UserData):
    return f"https://t.me/{user.usernames[0]}" if user.usernames else f"tg://user?id={user.id}"


def user_mention_html(user: UserData, name: str | None = None) -> str:
    return markdown.hlink(name or user.name, user_url(user))


def user_mention_markdown(user: UserData, name: str | None = None) -> str:
    return markdown.hlink(name or user.name, user_url(user))


async def fetch_user(bot: Bot, id: int) -> UserData:
    try:
        chat = await bot.get_chat(id)
    except TelegramBadRequest as ex:
        with contextlib.suppress(Exception):
            await user_manager.remove_user(id)
        for group in await group_manager.get_groups():
            with contextlib.suppress(Exception):
                group.members.remove(id)
                await group_manager.update_group(group)
        raise ChatDeleted from ex
    return await user_manager.update_from_chat(chat)


async def fetch_group(bot: Bot, id: int) -> GroupData:
    try:
        chat = await bot.get_chat(id)
    except TelegramBadRequest as ex:
        with contextlib.suppress(Exception):
            await group_manager.remove_group(id)
        raise ChatDeleted from ex
    return await group_manager.update_group_from_chat(chat)


async def fetch_member(bot: Bot, group: int, member: int, check_user: bool = False) -> UserData:
    try:
        chat_member = await bot.get_chat_member(group, member)
        assert chat_member.status not in [ChatMemberStatus.KICKED, ChatMemberStatus.LEFT]
        user = await (
            fetch_user(bot, member)
            if check_user
            else user_manager.update_from_user(chat_member.user)
        )
    except (TelegramBadRequest, ChatDeleted, AssertionError) as ex:
        await group_manager.remove_member(group, member)
        raise ChatDeleted from ex
    await group_manager.add_member(group, user.id)
    return user


async def parse_user(exp: str, bot: Bot | None = None) -> UserData:
    if id := exception.try_or_default(lambda: int(exp)):
        user = await user_manager.get_user(id)
    try:
        user = await user_manager.get_user_from_username(exp.removeprefix("@"))
    except NoResultFound as ex:
        raise ChatNotFound from ex
    if bot:
        return await fetch_user(bot, user.id)
    return user


async def parse_member(exp: str, group: int, bot: Bot | None = None) -> UserData:
    if id := exception.try_or_default(lambda: int(exp)):
        member = await user_manager.get_user(id)
    try:
        member = await user_manager.get_user_from_username(exp.removeprefix("@"))
    except NoResultFound as ex:
        raise ChatNotFound from ex
    data = await group_manager.get_group(group)
    if bot:
        return await fetch_member(bot, group, member.id)
    if member.id not in data.members:
        raise ChatNotFound
    return member
