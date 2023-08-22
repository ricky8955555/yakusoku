from aiogram.types import Chat, User

from yakusoku.utils import exception


class ChatNotFoundError(Exception):
    pass


def get_mention_html(chat: Chat | User, name: str | None = None) -> str:
    return (  # type: ignore
        exception.try_or_default(  # type: ignore
            lambda: chat.get_mention(
                name if name else chat.full_name, as_html=True  # type: ignore
            ),
        )
        or f'<a href="https://t.me/{chat.username}">{name or chat.full_name}</a>'
        if chat.username
        else name or chat.full_name
    )
