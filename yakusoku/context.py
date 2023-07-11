import contextlib
from typing import Any

_context = dict[str, Any]()


def set(name: str, data: Any) -> None:
    global _context
    _context[name] = data


def try_get(name: str) -> Any | None:
    return _context.get(name)


def get(name: str) -> Any:
    return _context[name]


def unset(name: str) -> None:
    with contextlib.suppress(KeyError):
        del _context[name]
