from typing import Callable, TypeVar

from aiogram.types import Chat

from yakusoku.shared import user_factory
from yakusoku.utils import chat, function

from .factory import WaifuFactory, WaifuGlobalProperty, WaifuLocalProperty

_T = TypeVar("_T")


def local_or_global(
    factory: WaifuFactory,
    key: Callable[[WaifuLocalProperty | WaifuGlobalProperty], _T | None],
    chat: int,
    member: int,
) -> _T | None:
    local = key(factory.get_waifu_local_property(chat, member))
    global_ = key(factory.get_waifu_global_property(member))
    return global_ if local is None else local


async def get_mentioned_member(group: Chat, username: str) -> Chat:
    assert (
        member := await function.try_invoke_or_default_async(
            lambda: chat.get_chat(group.bot, username)
        )
    ) and member.id in user_factory.get_members(group.id)
    return member
