from aiogram import Bot
from aiogram.types import PhotoSize
from cashews.wrapper import Cache

from yakusoku.archive.config import config


class AvatarManager:
    _cache: Cache

    def __init__(self) -> None:
        self._cache = Cache()
        self._cache.setup("mem://")
        # fmt: off
        setattr(
            self, "get_avatar_file",
            self._cache(ttl=config.avatar_ttl, key="user:{user}")(self.get_avatar_file),
        )
        # fmt: on

    async def get_avatar_file(self, bot: Bot, user: int) -> PhotoSize | None:
        avatars = await bot.get_user_profile_photos(user)
        return avatars.photos[0][0] if avatars.photos else None
