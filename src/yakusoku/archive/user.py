import sqlmodel
from aiogram.types import Chat, User
from sqlalchemy.exc import NoResultFound

from yakusoku.archive.models import UserData
from yakusoku.constants import FILTERED_IDS
from yakusoku.database import SQLSessionManager


class UserManager:
    sql: SQLSessionManager

    def __init__(self, sql: SQLSessionManager) -> None:
        self.sql = sql

    @staticmethod
    def _is_recordable(id: int) -> bool:
        return id > 0 and id not in FILTERED_IDS

    async def get_user_from_username(self, username: str) -> UserData:
        async with self.sql.session() as session:
            statement = sqlmodel.select(UserData).where(
                UserData.usernames.contains(username)  # type: ignore
            )
            results = await session.execute(statement)
            return results.one()[0]

    async def get_user(self, id: int) -> UserData:
        async with self.sql.session() as session:
            statement = sqlmodel.select(UserData).where(UserData.id == id)
            results = await session.execute(statement)
            return results.one()[0]

    async def get_users(self) -> list[UserData]:
        async with self.sql.session() as session:
            statement = sqlmodel.select(UserData)
            results = await session.execute(statement)
            return [row[0] for row in results.all()]

    async def update_user(self, user: UserData) -> None:
        if not UserManager._is_recordable(user.id):
            return
        async with self.sql.session() as session:
            session.add(user)
            await session.commit()
            await session.refresh(user)

    async def update_from_user(self, user: User) -> UserData:
        try:
            data = await self.get_user(user.id)
            data.update_from_user(user)
        except NoResultFound:
            data = UserData.from_user(user)
        await self.update_user(data)
        return data

    async def update_from_chat(self, chat: Chat) -> UserData:
        try:
            data = await self.get_user(chat.id)
            data.update_from_chat(chat)
        except NoResultFound:
            data = UserData.from_chat(chat)
        await self.update_user(data)
        return data

    async def remove_user(self, id: int) -> None:
        async with self.sql.session() as session:
            statement = sqlmodel.select(UserData).where(UserData.id == id)
            results = await session.execute(statement)
            await session.delete(results.one()[0])
            await session.commit()
