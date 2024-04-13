import sqlmodel

from yakusoku.database import SQLSessionManager
from yakusoku.module import ModuleConfig

from .models import SwitchConfig


class SwitchManager:
    sql: SQLSessionManager

    def __init__(self, sql: SQLSessionManager) -> None:
        self.sql = sql

    async def get_switch_config(self, group: int, module: ModuleConfig) -> SwitchConfig:
        async with self.sql.session() as session:
            statement = (
                sqlmodel.select(SwitchConfig)
                .where(SwitchConfig.group == group)
                .where(SwitchConfig.module == module.name)
            )
            results = await session.execute(statement)
            return (
                row[0]
                if (row := results.one_or_none())
                else SwitchConfig(group=group, module=module.name, enabled=module.default_enabled)
            )

    async def update_switch_config(self, config: SwitchConfig) -> None:
        async with self.sql.session() as session:
            session.add(config)
            await session.commit()
            await session.refresh(config)
