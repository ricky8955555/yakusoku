from aiogram import Bot
from aiogram.types import Chat, ChatMember

from yakusoku.shared import user_factory
from yakusoku.utils import function


def get_mention_html(chat: Chat, name: str | None = None) -> str:
    return (  # type: ignore
        function.try_invoke_or_default(  # type: ignore
            lambda: chat.get_mention(name, as_html=True),  # type: ignore
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
    assert chat, f"failed to get chat from username {chat_id}"
    user_factory.update_chat(chat := await bot.get_chat(chat_id))
    return chat


async def get_chat_member(bot: Bot, chat_id: int | str, user_id: int) -> ChatMember:
    member = await bot.get_chat_member(chat_id, user_id)
    user_factory.update_user(member.user)
    if isinstance(chat_id, int):
        user_factory.add_member(chat_id, user_id)
    return member


async def get_member(chat: Chat, user_id: int) -> ChatMember:
    member = await chat.get_member(user_id)
    user_factory.update_user(member.user)
    user_factory.add_member(chat.id, user_id)
    return member


async def get_member_from_username(group: Chat, username: str) -> ChatMember:
    assert (
        member := (
            await group.get_member(id)
            if (id := user_factory.get_user(username.lstrip("@")))
            else None
        )
    ), f"failed to get member from group {group.id} by username {username}"
    return member
