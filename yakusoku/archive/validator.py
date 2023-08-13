import contextlib

from aiogram import Bot
from aiogram.utils.exceptions import BadRequest, ChatNotFound

from yakusoku.archive import group_manager, user_manager


async def is_valid_user(bot: Bot, id: int) -> bool:
    try:
        chat = await bot.get_chat(id)
    except ChatNotFound:
        with contextlib.suppress(Exception):
            await user_manager.remove_user(id)
        for group in await group_manager.get_groups():
            with contextlib.suppress(Exception):
                group.members.remove(id)
                await group_manager.update_group(group)
        return False
    await user_manager.update_from_chat(chat)
    return True


async def is_valid_group(bot: Bot, id: int) -> bool:
    try:
        chat = await bot.get_chat(id)
    except ChatNotFound:
        with contextlib.suppress(Exception):
            await group_manager.remove_group(id)
        return False
    await group_manager.update_group_from_chat(chat)
    return True


async def is_valid_member(bot: Bot, group: int, member: int) -> bool:
    try:
        chat = await bot.get_chat_member(group, member)
    except BadRequest as ex:
        if ex.args[0] != "User not found":
            await group_manager.remove_member(group, member)
        return False
    await user_manager.update_from_user(chat.user)
    return True
