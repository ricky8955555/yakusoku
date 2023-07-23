from aiogram import Bot
from aiogram.types import Chat, ChatMember, User

from yakusoku.shared import user_factory
from yakusoku.utils import function


class ChatNotFoundError(Exception):
    pass


def get_mention_html(chat: Chat | User, name: str | None = None) -> str:
    return (  # type: ignore
        function.try_invoke_or_default(  # type: ignore
            lambda: chat.get_mention(
                name if name else chat.full_name, as_html=True  # type: ignore
            ),
        )
        or f'<a href="https://t.me/{chat.username}">{name or chat.full_name}</a>'
        if chat.username
        else name or chat.full_name
    )


async def get_chat(bot: Bot, chat_id: int | str) -> Chat:
    chat = await function.try_invoke_or_default_async(lambda: bot.get_chat(chat_id))
    if isinstance(chat_id, str):
        chat = (
            await bot.get_chat(id) if (id := user_factory.get_user(chat_id.lstrip("@"))) else None
        )
    if not chat:
        if isinstance(chat_id, int):
            user_factory.remove_user(chat_id)
        raise ChatNotFoundError
    user_factory.update_chat(chat)
    return chat


async def get_chat_member(bot: Bot, chat_id: int | str, user_id: int) -> ChatMember:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
    except Exception as ex:
        raise ChatNotFoundError from ex
    user_factory.update_user(member.user)
    if isinstance(chat_id, int):
        user_factory.add_member(chat_id, user_id)
    return member


async def get_member(chat: Chat, user_id: int) -> ChatMember:
    try:
        member = await chat.get_member(user_id)
    except Exception as ex:
        raise ChatNotFoundError from ex
    user_factory.update_user(member.user)
    user_factory.add_member(chat.id, user_id)
    return member


async def get_member_from_username(group: Chat, username: str) -> ChatMember:
    if not (
        member := (
            await group.get_member(id)
            if (id := user_factory.get_user(username.lstrip("@")))
            else None
        )
    ):
        raise ChatNotFoundError
    return member
