import sqlmodel
from aiogram.types import Chat
from sqlalchemy.exc import NoResultFound

from yakusoku.context import sql
from yakusoku.archive.models import GroupData


class GroupManager:
    def __init__(self) -> None:
        pass

    async def update_group_from_chat(self, chat: Chat) -> GroupData:
        try:
            data = await self.get_group(chat.id)
            data.update_from_chat(chat)
        except NoResultFound:
            data = GroupData.from_chat(chat)
        await self.update_group(data)
        return data

    async def update_group(self, group: GroupData) -> None:
        async with sql.session() as session:
            session.add(group)
            await session.commit()
            await session.refresh(group)

    async def get_group(self, id: int) -> GroupData:
        async with sql.session() as session:
            statement = sqlmodel.select(GroupData).where(GroupData.id == id)
            results = await session.execute(statement)
            return results.one()[0]

    async def get_groups(self) -> list[GroupData]:
        async with sql.session() as session:
            statement = sqlmodel.select(GroupData)
            results = await session.execute(statement)
            return [row[0] for row in results.all()]

    async def remove_group(self, id: int) -> None:
        async with sql.session() as session:
            statement = sqlmodel.select(GroupData).where(GroupData.id == id)
            results = await session.execute(statement)
            await session.delete(results.one()[0])
            await session.commit()

    async def add_member(self, group: int, member: int) -> None:
        data = await self.get_group(group)
        if member in data.members:
            return
        members = list(data.members)
        members.append(member)
        data.members = members
        await self.update_group(data)

    async def remove_member(self, group: int, member: int) -> None:
        data = await self.get_group(group)
        if member not in data.members:
            return
        members = list(data.members)
        members.remove(member)
        data.members = members
        await self.update_group(data)
