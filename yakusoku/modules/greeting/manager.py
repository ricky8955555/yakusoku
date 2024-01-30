import sqlmodel

from yakusoku import sql

from .models import GreetingConfig, GreetingData


class GreetingManager:
    def __init__(self):
        pass

    async def get_greeting_data(self, user: int) -> GreetingData:
        async with sql.session() as session:
            statement = sqlmodel.select(GreetingData).where(GreetingData.user == user)
            results = await session.execute(statement)
            return row[0] if (row := results.one_or_none()) else GreetingData(user=user)

    async def get_greeting_config(self, group: int) -> GreetingConfig:
        async with sql.session() as session:
            statement = sqlmodel.select(GreetingConfig).where(GreetingConfig.group == group)
            results = await session.execute(statement)
            return row[0] if (row := results.one_or_none()) else GreetingConfig(group=group)

    async def update_greeting_data(self, data: GreetingData) -> None:
        async with sql.session() as session:
            session.add(data)
            await session.commit()
            await session.refresh(data)

    async def update_greeting_config(self, config: GreetingConfig) -> None:
        async with sql.session() as session:
            session.add(config)
            await session.commit()
            await session.refresh(config)
