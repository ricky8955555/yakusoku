import sqlmodel

from yakusoku.database import SQLSessionManager

from .models import GreetingData


class GreetingManager:
    sql: SQLSessionManager

    def __init__(self, sql: SQLSessionManager):
        self.sql = sql

    async def get_greeting_data(self, user: int) -> GreetingData:
        async with self.sql.session() as session:
            statement = sqlmodel.select(GreetingData).where(GreetingData.user == user)
            results = await session.execute(statement)
            return row[0] if (row := results.one_or_none()) else GreetingData(user=user)

    async def update_greeting_data(self, data: GreetingData) -> None:
        async with self.sql.session() as session:
            session.add(data)
            await session.commit()
            await session.refresh(data)
