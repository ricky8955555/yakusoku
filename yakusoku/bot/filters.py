from aiogram.dispatcher.filters import Filter
from aiogram.types import CallbackQuery


class CallbackQueryFilter(Filter):
    header: str

    def __init__(self, header: str) -> None:
        self.header = header

    async def check(self, query: CallbackQuery) -> bool:  # type: ignore
        return query.data.startswith(self.header)
