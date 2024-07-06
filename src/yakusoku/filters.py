from aiogram import F
from aiogram.enums import ChatType
from aiogram.filters import Filter
from aiogram.types import CallbackQuery, ChatMemberUpdated, InlineQuery, Message

from yakusoku.context import bot_config


class AdminFilter(Filter):
    async def __call__(
        self, obj: Message | CallbackQuery | InlineQuery | ChatMemberUpdated
    ) -> bool:
        if getattr(obj, "sender_chat", None):
            return False

        if obj.from_user is None:
            return False

        if isinstance(obj, Message):
            chat = obj.chat
        elif isinstance(obj, CallbackQuery) and obj.message:
            chat = obj.message.chat
        elif isinstance(obj, ChatMemberUpdated):
            chat = obj.chat
        else:
            return False

        admins = await chat.get_administrators()
        return any(admin.user.id == obj.from_user.id for admin in admins)


GroupFilter = F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP])
OwnerFilter = F.from_user.id == bot_config.owner
NonAnonymousFilter = F.sender_chat.is_(None) & F.from_user.is_not(None)
ManagerFilter = GroupFilter & OwnerFilter & AdminFilter
