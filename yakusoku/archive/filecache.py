import os

from aiogram import Bot
from aiogram.types import File, PhotoSize


class FileCacheManager:
    path: str

    def __init__(self, path: str) -> None:
        self.path = path

    def _get_path(self, file_unique_id: str) -> str:
        return os.path.join(self.path, file_unique_id)

    async def get_file(self, bot: Bot, file: File | PhotoSize) -> str:
        path = self._get_path(file.file_unique_id)
        if not os.path.exists(path):
            await bot.download(file, destination=path)
        return path

    def get_cached_file(self, file_unique_id: str) -> str | None:
        return path if os.path.exists(path := self._get_path(file_unique_id)) else None
