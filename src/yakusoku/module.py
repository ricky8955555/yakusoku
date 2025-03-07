import importlib
import inspect
import os
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from aiogram import Bot, Router
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
    _router: Router
    _modules: dict[str, ModuleInfo]

    @property
    def loaded_modules(self) -> dict[str, ModuleInfo]:
        return dict(self._modules)

    @property
    def root_router(self) -> Router:
        return self._router

    def __init__(self, root_router: Router) -> None:
        self._router = root_router
        self._modules = {}

    @staticmethod
    def _collect_modules(path: Path) -> set[str]:
        # it only collects modules in the root of specific path located in current working path.
        path = path.absolute().relative_to(os.getcwd())
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

    def import_modules_from(self, path: Path) -> None:
        modules = self._collect_modules(path)
        self.import_modules(*modules)

    def create_router(self, name: str | None = None) -> Router:
        if not name:
            caller = inspect.stack()[1]
            module = inspect.getmodule(caller.frame)
            name = module.__name__ if module else None
        router = Router(name=name)
        return self._router.include_router(router)

    async def register_commands(self, bot: Bot) -> None:
        commands = [
            BotCommand(command=command, description=description)
            for info in self._modules.values()
            for (command, description) in info.config.commands.items()
        ]
        await bot.set_my_commands(commands)
