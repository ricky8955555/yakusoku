from typing import Awaitable, Callable, TypeVar

_PT = TypeVar("_PT")
_RT = TypeVar("_RT")
_T = TypeVar("_T")


def try_invoke_or_fallback(func: Callable[[_PT], _RT], param: _PT) -> _RT | _PT:
    try:
        return func(param)
    except Exception:
        return param


async def try_invoke_or_fallback_async(
    func: Callable[[_PT], Awaitable[_RT]], param: _PT
) -> _RT | _PT:
    try:
        return await func(param)
    except Exception:
        return param


def try_invoke_or_default(func: Callable[[], _RT], default: _T = None) -> _RT | _T:
    try:
        return func()
    except Exception:
        return default


async def try_invoke_or_default_async(
    func: Callable[[], Awaitable[_RT]], default: _T = None
) -> _RT | _T:
    try:
        return await func()
    except Exception:
        return default
