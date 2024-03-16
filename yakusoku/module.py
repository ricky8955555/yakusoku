from dataclasses import dataclass
import importlib
import os
from pathlib import Path
from types import ModuleType

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
    main: ModuleType
    config: ModuleConfig


class ModuleManager:
    _dispatcher: Dispatcher
    _modules: dict[ModuleType, ModuleInfo]
    _names: dict[str, ModuleType]

    @property
    def loaded_modules(self) -> set[ModuleType]:
        return set(self._modules.keys())

    def __init__(self, dispatcher: Dispatcher) -> None:
        self._dispatcher = dispatcher
        self._modules = {}

    def dispatcher(self) -> Dispatcher:
        return self._dispatcher

    @staticmethod
    def _collect_modules(path: str | Path) -> set[str]:
        # it only collects modules in the root of specific path located in current working path.
        path = Path(path).absolute().relative_to(Path(os.getcwd()))
        assert path.is_dir(), "attempt to collect modules from a non-directory path."
        modules = [
            item.with_suffix("").as_posix().replace("/", ".")
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

    def _get_config(self, module: ModuleType) -> ModuleConfig:
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
            main = importlib.import_module(f"{name}.main")
            config = self._get_config(base)
            info = ModuleInfo(main, config)
            self._modules[base] = info

    def import_modules_from(self, path: str | Path) -> None:
        modules = self._collect_modules(path)
        self.import_modules(*modules)

    async def register_commands(self) -> None:
        commands = [
            BotCommand(command, description)
            for info in self._modules.values()
            for (command, description) in info.config.commands.items()
        ]
        await self._dispatcher.bot.set_my_commands(commands)
