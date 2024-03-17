from typing import Any

from aiogram.dispatcher.filters import Filter
from aiogram.types import Chat, ChatType, Message

from yakusoku.dot.switch import switch_manager
from yakusoku.module import ModuleConfig


class SwitchFilter(Filter):
    _module: ModuleConfig

    def __init__(self, module: ModuleConfig):
        self._module = module

    async def check(self, *args: Any) -> bool:
        if not args:
            return True
        update = args[0]
        chat: Chat | None = getattr(update, "chat", None)
        if not chat:
            message: Message | None = getattr(update, "message", None)
            if not message:
                return True
            chat = message.chat
        if chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return True
        config = await switch_manager.get_switch_config(chat.id, self._module)
        return config.enabled
