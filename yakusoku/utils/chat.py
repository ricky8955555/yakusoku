from aiogram.types import Chat, User
from aiogram.utils import markdown

from yakusoku.utils import exception


class ChatNotFoundError(Exception):
    pass


def get_mention(chat: Chat | User, name: str | None = None, as_html: bool = True) -> str:
    return (  # type: ignore
        exception.try_or_default(  # type: ignore
            lambda: chat.get_mention(
                name if name else chat.full_name, as_html=as_html  # type: ignore
            ),
        )
        or (
            (markdown.hlink if as_html else markdown.link)(
                name or chat.full_name,  # type: ignore
                f"https://t.me/{chat.username}",
            )
            if chat.username
            else name or chat.full_name
        )
    )
