import importlib
import inspect
import logging
import os
import traceback
from pathlib import Path
from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from aiogram.dispatcher.event.telegram import TelegramEventObserver

from yakusoku import environ
from yakusoku.dot.patch import patch, patched
from yakusoku.dot.switch.filter import SwitchFilter
from yakusoku.module import ModuleManager

logger = logging.getLogger()


@patch(TelegramEventObserver)
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
    def register(
        self: Any,
        callback: CallbackType,
        *filters: CallbackType,
        flags: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> CallbackType:
        module = PatchedHandler._resolve_module(environ.module_path, inspect.stack())
        if module:
            try:
                base = importlib.import_module(module)
                config = ModuleManager.get_config(base)
                if config.can_disable:
                    filters = (SwitchFilter(config), *filters)
                else:
                    logging.debug(
                        f"ignored callback '{callback.__name__}' at '{module}' in switch patching for module can't disable."
                    )
            except Exception:
                logging.error(f"failed to patch callback '{callback}' in switch patching.")
                traceback.print_exc()
        else:
            module = inspect.getmodule(callback)
            logging.debug(
                f"ignored callback '{callback.__name__}' at '{module and module.__name__}' in switch patching for module was not found."
            )
        return self.__old_register(callback, *filters, flags=flags, **kwargs)
