from typing import Any

from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import Chat, Message

from yakusoku.dot.switch import switch_manager
from yakusoku.module import ModuleConfig


class SwitchFilter(Filter):
    _module: ModuleConfig

    def __init__(self, module: ModuleConfig) -> None:
        self._module = module

    async def __call__(self, obj: Any) -> bool:
        chat: Chat | None = getattr(obj, "chat", None)
        if not chat:
            message: Message | None = getattr(obj, "message", None)
            if not message:
                return True
            chat = message.chat
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return True
        config = await switch_manager.get_switch_config(chat.id, self._module)
        return config.enabled
