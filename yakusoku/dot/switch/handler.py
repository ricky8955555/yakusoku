import importlib
import inspect
from typing import Any
from aiogram.dispatcher.filters import Filter
from aiogram.dispatcher.handler import Handler

from yakusoku.dot.patch import patch, patched
from yakusoku.dot.switch.filter import SwitchFilter
from yakusoku.module import ModuleManager


@patch(Handler)
class PatchedHandler:
    @patched
    def register(self: Any, handler: Any, filters: list[Filter] | None = None, index: Any = None):
        if not filters:
            filters = []
        main = inspect.getmodule(handler)
        try:
            assert main and main.__package__
            base = importlib.import_module(main.__package__)
            config = ModuleManager.get_config(base)
            if config.can_disable:
                filters.insert(0, SwitchFilter(config))
        except AssertionError:
            print(f"ignored handler '{handler}' in switch patching.")
        return self.__old_register(handler, filters, index)
