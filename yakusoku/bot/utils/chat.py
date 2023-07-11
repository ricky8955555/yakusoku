from aiogram import Bot
from aiogram.types import Chat

from ..shared import users
from . import function


async def get_chat_from_username(bot: Bot, username: str) -> Chat:
    assert (
        chat := (
            (await bot.get_chat(id) if (id := users.get_user(username.lstrip("@"))) else None)
            or await function.try_invoke_or_default_async(lambda: bot.get_chat(username))
        )
    ), f"failed to get user id from username {username}"
    return chat
