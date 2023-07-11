from aiogram import Bot
from aiogram.types import Chat

from ..shared import users
from . import function


def get_mention_html(chat: Chat, name: str | None = None) -> str:
    return (  # type: ignore
        function.try_invoke_or_default(  # type: ignore
            lambda: chat.get_mention(name, as_html=True),  # type: ignore
        )
        or f'<a href="https://t.me/{chat.username}">{name or chat.full_name}</a>'
        if chat.username
        else name or chat.full_name
    )


async def get_chat_from_username(bot: Bot, username: str) -> Chat:
    assert (
        chat := (
            (await bot.get_chat(id) if (id := users.get_user(username.lstrip("@"))) else None)
            or await function.try_invoke_or_default_async(lambda: bot.get_chat(username))
        )
    ), f"failed to get user id from username {username}"
    return chat
