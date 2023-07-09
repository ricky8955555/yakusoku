from typing import Any, TypeVar

_T = TypeVar("_T")
_context = dict[str, Any]()


def set(name: str, data: Any) -> None:
    global _context
    _context[name] = data


def try_get(name: str) -> Any | None:
    data = _context.get(name)
    assert data, "context was requested before context initialized"
    return data


def get(name: str) -> Any:
    return _context[name]
