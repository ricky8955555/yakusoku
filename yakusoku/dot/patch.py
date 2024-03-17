import inspect
from typing import Any, Callable, TypeVar

_T = TypeVar("_T")


def patch(target: type) -> Callable[[type[_T]], type[_T]]:
    def is_patched(field: Any) -> bool:
        return getattr(field, "__patched__", False)

    def decorator(cls: type[_T]) -> type[_T]:
        for name, field in inspect.getmembers(cls, is_patched):
            old = getattr(target, name, None)
            setattr(target, f"_{cls.__name__}__old_{name}", old)
            setattr(target, name, field)
        return cls

    return decorator


def patched(field: Any) -> Any:
    setattr(field, "__patched__", True)
    return field
