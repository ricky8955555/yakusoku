from aiogram.types import Chat, User
from aiogram.utils import markdown


class ChatNotFoundError(Exception):
    pass


def mention_html(chat: Chat | User, name: str | None = None) -> str:
    if isinstance(chat, User):
        return chat.mention_html(name or chat.full_name)
    else:
        return (
            markdown.hlink(name or chat.full_name, f"https://t.me/{chat.username}")
            if chat.username
            else name or chat.full_name
        )


def mention_markdown(chat: Chat | User, name: str | None = None) -> str:
    if isinstance(chat, User):
        return chat.mention_markdown(name or chat.full_name)
    else:
        return (
            markdown.link(name or chat.full_name, f"https://t.me/{chat.username}")
            if chat.username
            else name or chat.full_name
        )
