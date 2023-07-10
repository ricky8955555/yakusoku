import re
from typing import AsyncIterable

from aiogram import Bot
from aiogram.types import Chat, Message

from ..shared import users
from . import function


async def get_chat_from_username(bot: Bot, username: str) -> Chat:
    assert (
        chat := (
            (
                await bot.get_chat(id)
                if (id := users.get_user(username.lstrip("@")))
                else None
            )
            or await function.try_invoke_or_default_async(
                lambda: bot.get_chat(username)
            )
        )
    ), f"failed to get user id from username {username}"
    return chat


def get_mentioned_usernames(message: str) -> list[str]:
    return re.findall(r"(@\w+)", message)


async def get_mentioned_chats(message: Message) -> AsyncIterable[Chat]:
    usernames = get_mentioned_usernames(message.text)
    return (
        chat
        async for chat in (
            await function.try_invoke_or_default_async(
                lambda: get_chat_from_username(message.bot, name)
            )
            for name in usernames
        )
        if chat
    )
