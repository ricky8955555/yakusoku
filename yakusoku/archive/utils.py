from typing import AsyncIterable

from yakusoku.archive import group_manager, user_manager
from yakusoku.archive.models import UserData


async def get_members(group: int) -> AsyncIterable[UserData]:
    data = await group_manager.get_group(group)
    for member in data.members:
        yield await user_manager.get_user(member)


async def get_user_members(group: int) -> AsyncIterable[UserData]:
    return (member async for member in get_members(group) if not member.is_bot)


def user_mention_html(user: UserData, name: str | None = None) -> str:
    if user.usernames:
        return f'<a href="https://t.me/{user.usernames[0]}">{name or user.name}</a>'
    else:
        return f'<a href="tg://user?id={user.id}>{name or user.name}</a>'
