from typing import Any

from aiogram.types import CallbackQuery

from yakusoku.dot.patch import patch, patched


@patch(CallbackQuery)
class PatchedCallbackQuery:
    @patched
    def __init__(self: Any, conf: dict[str, Any], **kwargs: Any):
        self.__old_init__(conf, **kwargs)
        setattr(self.message, "_from_callback_query", self)
