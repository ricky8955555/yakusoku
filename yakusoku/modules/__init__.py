import importlib
import os
from pathlib import Path
from typing import Any

from aiogram import Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault

MODULES_PATH = os.path.dirname(__file__)
MODULES_BASE_PACKAGE = __loader__.name


_commands: dict[str, str] = {}
_dispatcher: Dispatcher | None = None


def _get_modules() -> set[str]:
    modules = [
        item.stem + ".main"
        for item in Path(MODULES_PATH).iterdir()
        if (item.is_dir() and (item / "__init__.py").exists() and (item / "main.py").exists())
    ]
    modules_set = set(modules)
    assert len(modules_set) == len(modules), "duplicated modules were detected"
    return modules_set


def _import_modules() -> None:
    for module in _get_modules():
        importlib.import_module(f"{MODULES_BASE_PACKAGE}.{module}")


def load(dp: Dispatcher) -> None:
    global _dispatcher
    _dispatcher = dp
    _import_modules()


def command_handler(  # type: ignore
    commands: list[str],
    summary: str,
    *args: Any,
    **kwargs: Any,
):
    update_command(commands[0], summary)
    return dispatcher().message_handler(*args, **kwargs, commands=commands)  # type: ignore


def update_command(command: str, summary: str) -> None:
    _commands[command] = summary


async def register_commands() -> None:
    await dispatcher().bot.set_my_commands(
        [BotCommand(command, summary) for command, summary in _commands.items()],
        BotCommandScopeDefault(),
    )


def dispatcher() -> Dispatcher:
    assert _dispatcher, "get dispatcher before initialization"
    return _dispatcher
