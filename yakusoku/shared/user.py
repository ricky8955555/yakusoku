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

    def _update_info_from_user(self, info: UserInfo, user: User) -> UserInfo:
        info = dataclasses.replace(
            info,
            name=user.full_name,
        )
        if user.username:
            info.usernames.add(user.username)
        return info

    def update_user(self, user: User) -> None:
        info = self.get_userinfo(user.id)
        info = self._update_info_from_user(info, user)
        self._user_info_db[user.id] = info.to_database()
        if user.username:
            self._user_db[user.username] = user.id

    def _get_chat_photo_id(self, photo: ChatPhoto) -> str:
        return (
            photo.big_file_unique_id
            if self._config.cache_big_avatar
            else photo.small_file_unique_id
        )

    def _update_info_from_chat(self, info: UserInfo, chat: Chat) -> UserInfo:
        return dataclasses.replace(
            info,
            name=chat.full_name,
            usernames=(set(chat.active_usernames) if chat.active_usernames else set()),
        )

    def update_chat(self, chat: Chat) -> None:
        if chat.type != "private":
            return
        info = self.get_userinfo(chat.id)
        avatar = self._get_chat_photo_id(chat.photo) if chat.photo else None
        info = self._update_info_from_chat(info, chat)
        if not info.avatar or avatar != info.avatar[0]:
            info = dataclasses.replace(
                info,
                avatar=(avatar, -1),  # force update
            )
        self._user_info_db[chat.id] = info.to_database()
        for username in chat.active_usernames or list[str]():
            self._user_db[username] = chat.id

    @staticmethod
    def _avatar_path(user: int) -> str:
        return os.path.join(AVATAR_PATH, str(user))

    async def _download_avatar(self, photo: ChatPhoto, path: str):
        if self._config.cache_big_avatar:
            await photo.download_big(path)
        else:
            await photo.download_small(path)

    async def get_avatar_file(
        self, user: User | Chat | tuple[int, Bot], lazy: bool = False, force: bool = False
    ) -> str | None:
        id, bot = user if isinstance(user, tuple) else (user.id, user.bot)
        info = self.get_userinfo(id)
        path = UserFactory._avatar_path(id)
        last_id = info.avatar[0] if info.avatar else None
        if info.avatar and (
            lazy
            or (
                not force
                and (
                    not (force := info.avatar[1] == -1)
                    and datetime.fromtimestamp(info.avatar[1]) - datetime.now()
                    >= timedelta(seconds=self._config.avatar_cache_lifespan)
                )
            )
        ):
            if not last_id:
                return None
            if os.path.exists(path):
                return path
        if not isinstance(user, Chat):
            user = await bot.get_chat(id)
        info = self._update_info_from_chat(info, user)
        if not user.photo:
            info = dataclasses.replace(info, avatar=(None, datetime.now().timestamp()))
            self._user_info_db[user.id] = info.to_database()
            return None
        new_id = self._get_chat_photo_id(user.photo)
        if force or last_id != new_id or not os.path.exists(path):
            await self._download_avatar(user.photo, path)
        info = dataclasses.replace(info, avatar=(new_id, datetime.now().timestamp()))
        self._user_info_db[user.id] = info.to_database()
        return path

    async def get_avatar(
        self, user: User | Chat | tuple[int, Bot], lazy: bool = False, force: bool = False
    ) -> IOBase | None:
        return (
            open(avatar, "rb")
            if (avatar := await self.get_avatar_file(user, lazy, force))
            else None
        )

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

    def remove_user(self, user: int) -> None:
        with contextlib.suppress(KeyError):
            del self._user_info_db[user]
        for username in (username for username, id in self._user_db.items() if id == user):
            del self._user_db[username]
        for group, members in self._member_db.items():
            with contextlib.suppress(KeyError):
                members.remove(user)
            self._member_db[group] = members
