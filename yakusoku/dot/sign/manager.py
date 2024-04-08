import sqlmodel

from yakusoku.context import sql

from .models import SignConfig


class SignManager:
    def __init__(self):
        pass

    async def get_sign_config(self, group: int) -> SignConfig:
        async with sql.session() as session:
            statement = sqlmodel.select(SignConfig).where(SignConfig.group == group)
            results = await session.execute(statement)
            return row[0] if (row := results.one_or_none()) else SignConfig(group=group)

    async def update_sign_config(self, config: SignConfig) -> None:
        async with sql.session() as session:
            session.add(config)
            await session.commit()
            await session.refresh(config)
