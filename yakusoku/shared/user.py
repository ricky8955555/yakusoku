import contextlib
import dataclasses
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from io import IOBase
from typing import Any

from aiogram import Bot
from aiogram.types import Chat, ChatPhoto, User

from yakusoku import database
from yakusoku.config import Config
from yakusoku.constants import DATA_PATH

DATABASE_NAME = "user"
AVATAR_PATH = os.path.join(DATA_PATH, "cache", "avatar")


os.makedirs(AVATAR_PATH, exist_ok=True)


@dataclass(frozen=True)
class _Config(Config):
    cache_big_avatar: bool = False
    avatar_cache_lifespan: int = 600


@dataclass(frozen=True)
class UserInfo:
    avatar: tuple[str | None, int] | None = None  # id, time
    name: str | None = None
    usernames: set[str] = dataclasses.field(default_factory=set)

    @staticmethod
    def from_database(data: tuple[Any, ...]) -> "UserInfo":
        return UserInfo(*data)

    def to_database(self) -> tuple[Any, ...]:
        return dataclasses.astuple(self)


class UserFactory:
    _member_db: dict[int, set[int]]
    _user_db: dict[str, int]
    _user_info_db: dict[int, tuple[Any, ...]]
    _config: _Config

    def __init__(self) -> None:
        self._member_db = database.get(DATABASE_NAME, "members")
        self._user_db = database.get(DATABASE_NAME, "users")
        self._user_info_db = database.get(DATABASE_NAME, "info")
        self._config = _Config.load("user")

    def get_members(self, chat: int) -> set[int]:
        return self._member_db.get(chat) or set()

    def clear_members(self, chat: int) -> None:
        with contextlib.suppress(KeyError):
            del self._member_db[chat]

    def get_user(self, username: str) -> int | None:
        if not username:
            raise ValueError
        return self._user_db.get(username)

    def get_userinfo(self, id: int) -> UserInfo:
        data = self._user_info_db.get(id)
        return UserInfo.from_database(data) if data else UserInfo()

    def update_user(self, user: User) -> None:
        if not user.username:
            raise ValueError
        info = self.get_userinfo(user.id)
        self._user_db[user.username] = user.id
        info = dataclasses.replace(info, name=user.full_name)
        info.usernames.add(user.username)
        self._user_info_db[user.id] = info.to_database()

    def _get_chat_photo_id(self, photo: ChatPhoto) -> str:
        return (
            photo.big_file_unique_id
            if self._config.cache_big_avatar
            else photo.small_file_unique_id
        )

    def update_chat(self, chat: Chat) -> None:
        if chat.type != "private":
            return
        info = self.get_userinfo(chat.id)
        info = dataclasses.replace(
            info,
            name=chat.full_name,
            avatar=(
                self._get_chat_photo_id(chat.photo) if chat.photo else None,
                datetime.now().timestamp(),
            ),
            usernames=set(chat.active_usernames),
        )
        self._user_info_db[chat.id] = info.to_database()

    @staticmethod
    def _avatar_path(user: int) -> str:
        return os.path.join(AVATAR_PATH, str(user))

    async def get_avatar(
        self, user: User | Chat | tuple[int, Bot], lazy: bool = False
    ) -> IOBase | None:
        id, bot = user if isinstance(user, tuple) else (user.id, user.bot)
        info = self.get_userinfo(id)
        path = UserFactory._avatar_path(id)
        avatar = info.avatar[0] if info.avatar else None
        if (
            info.avatar
            and (
                lazy
                or (
                    datetime.fromtimestamp(info.avatar[1]) - datetime.now()
                    >= timedelta(seconds=self._config.avatar_cache_lifespan)
                )
            )
            and os.path.exists(path)
        ):
            return open(path, "rb") if id else None
        if not isinstance(user, Chat):
            user = await bot.get_chat(id)
        self.update_chat(user)
        new_id = self._get_chat_photo_id(user.photo)
        if avatar != new_id or not os.path.exists(path):
            fp = open(path, "wb+")
            if self._config.cache_big_avatar:
                return await user.photo.download_big(fp)
            return await user.photo.download_small(fp)
        return open(path, "rb")

    async def get_avatar_file(
        self, user: User | Chat | tuple[int, Bot], lazy: bool = False
    ) -> str | None:
        fp = await self.get_avatar(user, lazy)
        if not fp:
            return None
        fp.close()
        return UserFactory._avatar_path(user[0] if isinstance(user, tuple) else user.id)

    def get_avatar_cache(self, user: int) -> IOBase | None:
        return open(path, "rb") if os.path.exists(path := UserFactory._avatar_path(user)) else None

    def get_avatar_cache_file(self, user: int) -> str | None:
        return path if os.path.exists(path := UserFactory._avatar_path(user)) else None

    # following code is strange
    # due to there is some troubles while handling set in SqliteDict

    def add_member(self, chat: int, member: int) -> None:
        members = self._member_db.get(chat) or set()
        members.add(member)
        self._member_db[chat] = members

    def remove_member(self, chat: int, member: int) -> None:
        with contextlib.suppress(KeyError):
            members = self._member_db[chat]
            members.remove(member)
            self._member_db[chat] = members
