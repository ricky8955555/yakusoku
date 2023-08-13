import os

from aiogram.types import File, PhotoSize

from yakusoku.constants import DATA_PATH

_FILE_CACHE_PATH = os.path.join(DATA_PATH, "filecache")

os.makedirs(_FILE_CACHE_PATH, exist_ok=True)


class FileCacheManager:
    def __init__(self) -> None:
        pass

    @staticmethod
    def _get_path(file_unique_id: str) -> str:
        return os.path.join(_FILE_CACHE_PATH, file_unique_id)

    async def get_file(self, file: File | PhotoSize) -> str:
        path = self._get_path(file.file_unique_id)
        if not os.path.exists(path):
            await file.download(destination_file=path)
        return path

    def get_cached_file(self, file_unique_id: str) -> str | None:
        return path if os.path.exists(path := self._get_path(file_unique_id)) else None
