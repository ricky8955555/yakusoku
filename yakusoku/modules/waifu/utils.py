from typing import Callable, TypeVar

from .factory import WaifuFactory, WaifuGlobalProperty, WaifuLocalProperty

_T = TypeVar("_T")


def local_or_global(
    factory: WaifuFactory,
    key: Callable[[WaifuLocalProperty | WaifuGlobalProperty], _T | None],
    chat: int,
    member: int,
) -> _T:
    local: _T | None = key(factory.get_waifu_local_property(chat, member))
    global_: _T = key(factory.get_waifu_global_property(member))  # type: ignore
    return global_ if local is None else local
