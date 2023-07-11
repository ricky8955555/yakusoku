from aiogram import Bot
from aiogram.types import Chat, User

from ..shared import users
from . import function


def get_chat_link(chat: Chat | User, name: str | None = None) -> str:
    return (
        f"[{name or chat.full_name}]({url})"
        if (url := (chat.user_url if isinstance(chat, Chat) else chat.url))  # type: ignore
        else name or chat.full_name  # type: ignore
    )


async def get_chat_from_username(bot: Bot, username: str) -> Chat:
    assert (
        chat := (
            (await bot.get_chat(id) if (id := users.get_user(username.lstrip("@"))) else None)
            or await function.try_invoke_or_default_async(lambda: bot.get_chat(username))
        )
    ), f"failed to get user id from username {username}"
    return chat
