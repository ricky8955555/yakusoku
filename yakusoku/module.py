import importlib
import os
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Any, Callable

from aiogram import Dispatcher
from aiogram.types import BotCommand


@dataclass(frozen=True, kw_only=True)
class ModuleConfig:
    name: str
    description: str
    commands: dict[str, str]
    default_enabled: bool = True
    can_disable: bool = True

    def __post_init__(self) -> None:
        assert (
            self.can_disable or self.default_enabled
        ), "'default_enabled' should be 'True' when 'can_disable' is set with 'True'."


@dataclass(frozen=True)
class ModuleInfo:
    base: ModuleType
    main: ModuleType
    config: ModuleConfig


class ModuleManager:
    _dispatcher: Dispatcher
    _modules: dict[str, ModuleInfo]
    _on_startups: list[Callable[[], Any]]
    _on_shutdowns: list[Callable[[], Any]]

    @property
    def loaded_modules(self) -> dict[str, ModuleInfo]:
        return dict(self._modules)

    def __init__(self, dispatcher: Dispatcher) -> None:
        self._dispatcher = dispatcher
        self._modules = {}
        self._on_startups = []
        self._on_shutdowns = []

        self.on_startup(self._register_commands)

    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @staticmethod
    def _collect_modules(path: str | Path) -> set[str]:
        # it only collects modules in the root of specific path located in current working path.
        path = Path(path).absolute().relative_to(os.getcwd())
        assert path.is_dir(), "attempt to collect modules from a non-directory path."
        modules = [
            ".".join(item.with_suffix("").parts)
            for item in Path(path).iterdir()
            if (
                (item.is_file() and item.suffix == ".py")
                or ((item / "__init__.py").exists() and (item / "main.py").exists())
            )
            and not item.stem.startswith("_")
        ]
        modules_set = set(modules)
        assert len(modules_set) == len(modules), "duplicate modules were detected."
        return modules_set

    @staticmethod
    def get_config(module: ModuleType) -> ModuleConfig:
        config = getattr(module, "__module_config__", None)
        assert (
            config is not None
        ), f"'__module_config__' is not found in module '{module.__name__}'."
        assert isinstance(
            config, ModuleConfig
        ), "'__module_config__' should be 'ModuleConfig' instance."
        return config

    def import_modules(self, *modules: str) -> None:
        for name in modules:
            base = importlib.import_module(name)
            config = self.get_config(base)
            assert (
                config.name not in self._modules
            ), f"module named '{config.name}' already existed."
            main = importlib.import_module(f"{name}.main")
            info = ModuleInfo(base, main, config)
            self._modules[config.name] = info

    def import_modules_from(self, path: str | Path) -> None:
        modules = self._collect_modules(path)
        self.import_modules(*modules)

    async def startup(self) -> None:
        for handler in self._on_startups:
            await handler()

    async def shutdown(self) -> None:
        for handler in self._on_shutdowns:
            await handler()

    def on_startup(self, handler: Callable[[], Any]) -> Callable[[], Any]:
        self._on_startups.append(handler)
        return handler

    def on_shutdown(self, handler: Callable[[], Any]) -> Callable[[], Any]:
        self._on_shutdowns.append(handler)
        return handler

    async def _register_commands(self) -> None:
        commands = [
            BotCommand(command, description)
            for info in self._modules.values()
            for (command, description) in info.config.commands.items()
        ]
        await self._dispatcher.bot.set_my_commands(commands)
