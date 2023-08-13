import contextlib
from typing import AsyncIterable

from aiogram import Bot
from aiogram.utils.exceptions import BadRequest, ChatNotFound

from yakusoku.archive import group_manager, user_manager
from yakusoku.archive.exceptions import ChatDeleted
from yakusoku.archive.models import GroupData, UserData


async def get_members(group: int) -> AsyncIterable[UserData]:
    data = await group_manager.get_group(group)
    for member in data.members:
        yield await user_manager.get_user(member)


async def get_user_members(group: int) -> AsyncIterable[UserData]:
    return (member async for member in get_members(group) if not member.is_bot)


def user_mention_html(user: UserData, name: str | None = None) -> str:
    if user.usernames:
        return f'<a href="https://t.me/{user.usernames[0]}">{name or user.name}</a>'
    else:
        return f'<a href="tg://user?id={user.id}>{name or user.name}</a>'


async def fetch_user(bot: Bot, id: int) -> UserData:
    try:
        chat = await bot.get_chat(id)
    except ChatNotFound as ex:
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
    except ChatNotFound as ex:
        with contextlib.suppress(Exception):
            await group_manager.remove_group(id)
        raise ChatDeleted from ex
    return await group_manager.update_group_from_chat(chat)


async def fetch_member(bot: Bot, group: int, member: int) -> UserData:
    try:
        chat = await bot.get_chat_member(group, member)
    except BadRequest as ex:
        if ex.args[0] != "User not found":
            raise
        await group_manager.remove_member(group, member)
        raise ChatDeleted from ex
    return await user_manager.update_from_user(chat.user)
