from aiogram.types import Chat, User
from aiogram.utils import markdown


class ChatNotFoundError(Exception):
    pass


def chat_url(chat: Chat | User) -> str | None:
    if isinstance(chat, User):
        return chat.url
    if chat.username:
        return f"https://t.me/{chat.username}"
    return None


def mention_html(chat: Chat | User, name: str | None = None) -> str:
    url = chat_url(chat)
    return markdown.hlink(name or chat.full_name, url) if url else name or chat.full_name


def mention_markdown(chat: Chat | User, name: str | None = None) -> str:
    url = chat_url(chat)
    return markdown.link(name or chat.full_name, url) if url else name or chat.full_name
