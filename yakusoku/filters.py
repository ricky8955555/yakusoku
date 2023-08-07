from aiogram.dispatcher.filters import AdminFilter, Filter
from aiogram.types import CallbackQuery, ChatMemberUpdated, InlineQuery, Message

from yakusoku import bot_config


class CallbackQueryFilter(Filter):
    header: str

    def __init__(self, header: str) -> None:
        self.header = header

    async def check(self, query: CallbackQuery) -> bool:  # type: ignore
        return query.data.startswith(self.header)


class ManagerFilter(AdminFilter):
    async def check(self, obj: Message | CallbackQuery | InlineQuery | ChatMemberUpdated) -> bool:
        from_id = obj.from_id if isinstance(obj, Message) else obj.from_user.id
        return from_id == bot_config.owner or await super().check(obj)


class NonAnonymousFilter(Filter):
    async def check(self, obj: Message) -> bool:  # type: ignore
        return not obj.sender_chat
