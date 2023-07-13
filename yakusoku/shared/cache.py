import os
from io import IOBase

from aiogram.types import ChatPhoto

from yakusoku.constants import DATA_PATH

CHAT_PHOTO_PATH = os.path.join(DATA_PATH, "chat_photo")

os.makedirs(CHAT_PHOTO_PATH, exist_ok=True)


async def get_big_chat_photo(photo: ChatPhoto) -> IOBase:
    file = os.path.join(CHAT_PHOTO_PATH, photo.big_file_unique_id)
    return (
        open(file, "rb")
        if os.path.exists(file)
        else await photo.download_big(open(file, "wb+"))
    )


async def get_small_chat_photo(photo: ChatPhoto) -> IOBase:
    file = os.path.join(CHAT_PHOTO_PATH, photo.small_file_unique_id)
    return (
        open(file, "rb")
        if os.path.exists(file)
        else await photo.download_small(open(file, "wb+"))
    )
