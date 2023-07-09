import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from aiogram import Dispatcher  # type: ignore

from .. import context


MODULES_PATH = os.path.dirname(__file__)
MODULES_BASE_PACKAGE = __loader__.name


@dataclass
class _ModuleContext:
    dispatcher: Dispatcher


def _set_context(data: _ModuleContext) -> None:
    context.set("_module", data)


def _get_modules() -> list[str]:
    return [
        item.stem
        for item in Path(MODULES_PATH).iterdir()
        if (item.is_dir() and (item / "__init__.py").exists())
        or (
            item.is_file() and item.suffix == ".py" and item.stem != "__init__"
        )
    ]


def _import_modules() -> None:
    for module in _get_modules():
        importlib.import_module(f"{MODULES_BASE_PACKAGE}.{module}")


def run(dp: Dispatcher) -> None:
    _set_context(_ModuleContext(dp))
    _import_modules()


def dispatcher() -> Dispatcher:
    return context.get("_module").dispatcher
