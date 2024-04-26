import importlib
import inspect
import os
import traceback
from pathlib import Path
from typing import Any

from aiogram.dispatcher.filters import Filter
from aiogram.dispatcher.handler import Handler

from yakusoku import environ
from yakusoku.dot.patch import patch, patched
from yakusoku.dot.switch.filter import SwitchFilter
from yakusoku.module import ModuleManager


@patch(Handler)
class PatchedHandler:
    @staticmethod
    def _resolve_module(module_path: Path, stacks: list[inspect.FrameInfo]) -> str | None:
        result: str | None = None
        for frame in stacks:
            path = Path(frame.filename)
            try:
                name = path.relative_to(module_path).parts[0]
            except ValueError:
                continue
            path = (module_path / name).relative_to(os.getcwd())
            package = ".".join(path.parts)
            assert not result or result == package, "more than one module found in stack."
            result = package
        return result

    @patched
    def register(self: Any, handler: Any, filters: list[Filter] | None = None, index: Any = None):
        if not filters:
            filters = []
        module = PatchedHandler._resolve_module(environ.module_path, inspect.stack())
        if module:
            try:
                base = importlib.import_module(module)
                config = ModuleManager.get_config(base)
                if config.can_disable:
                    filters.insert(0, SwitchFilter(config))
            except Exception:
                print(f"failed to patch handler '{handler}' in switch patching.")
                traceback.print_exc()
        else:
            print(f"ignored handler '{handler}' in switch patching.")
        return self.__old_register(handler, filters, index)
