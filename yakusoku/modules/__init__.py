import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from aiogram import Dispatcher
from aiogram.types import BotCommand, BotCommandScopeDefault

from yakusoku import context

MODULES_PATH = os.path.dirname(__file__)
MODULES_BASE_PACKAGE = __loader__.name


@dataclass(frozen=True)
class _ModuleContext:
    dispatcher: Dispatcher


def _set_context(data: _ModuleContext) -> None:
    context.set("_module", data)
    context.set("_commands", {})


def _get_modules() -> set[str]:
    modules = [
        item.stem
        for item in Path(MODULES_PATH).iterdir()
        if (item.is_dir() and (item / "__init__.py").exists())
        or (item.is_file() and item.suffix == ".py" and item.stem != "__init__")
    ]
    modules_set = set(modules)
    assert len(modules_set) == len(modules), "duplicated modules were detected"
    return modules_set


def _import_modules() -> None:
    for module in _get_modules():
        importlib.import_module(f"{MODULES_BASE_PACKAGE}.{module}")


def load(dp: Dispatcher) -> None:
    _set_context(_ModuleContext(dp))
    _import_modules()


def command_handler(  # type: ignore
    commands: list[str],
    description: str,
    *args: Any,
    **kwargs: Any,
):
    for command in commands:
        update_command(command, description)
    return dispatcher().message_handler(*args, **kwargs, commands=commands)  # type: ignore


def update_command(command: str, description: str) -> None:
    commands: dict[str, str] = context.get("_commands") or {}
    commands[command] = description
    context.set("_commands", commands)


async def register_commands() -> None:
    if commands := context.try_get("_commands"):
        await dispatcher().bot.set_my_commands(
            [BotCommand(command, description) for command, description in commands.items()],
            BotCommandScopeDefault(),
        )
    context.unset("_commands")


def dispatcher() -> Dispatcher:
    return context.get("_module").dispatcher
