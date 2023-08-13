from aiogram import Bot
from aiogram.types import PhotoSize
from cashews.wrapper import Cache

from yakusoku.archive.config import config

_cache = Cache()
_cache.setup("mem://")


class AvatarManager:
    def __init__(self) -> None:
        pass

    @_cache(ttl=config.avatar_ttl, key="user:{user}")
    async def get_avatar_file(self, bot: Bot, user: int) -> PhotoSize | None:
        avatars = await bot.get_user_profile_photos(user)
        return avatars.photos[0][0] if avatars.photos else None
