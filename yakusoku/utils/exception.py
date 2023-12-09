import traceback
from typing import Awaitable, Callable, TypeVar

_PT = TypeVar("_PT")
_RT = TypeVar("_RT")
_T = TypeVar("_T")


def try_or_fallback(
    func: Callable[[_PT], _RT], param: _PT, logging: bool = False
) -> _RT | _PT:
    try:
        return func(param)
    except Exception:
        if logging:
            traceback.print_exc()
        return param


async def try_or_fallback_async(
    func: Callable[[_PT], Awaitable[_RT]], param: _PT, logging: bool = False
) -> _RT | _PT:
    try:
        return await func(param)
    except Exception:
        if logging:
            traceback.print_exc()
        return param


def try_or_default(
    func: Callable[[], _RT], default: _T = None, logging: bool = False
) -> _RT | _T:
    try:
        return func()
    except Exception:
        if logging:
            traceback.print_exc()
        return default


async def try_or_default_async(
    func: Callable[[], Awaitable[_RT]], default: _T = None, logging: bool = False
) -> _RT | _T:
    try:
        return await func()
    except Exception:
        if logging:
            traceback.print_exc()
        return default
