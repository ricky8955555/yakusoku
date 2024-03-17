import sqlmodel

from yakusoku.context import sql
from yakusoku.module import ModuleConfig

from .models import SwitchConfig


class SwitchManager:
    def __init__(self):
        pass

    async def get_switch_config(self, group: int, module: ModuleConfig) -> SwitchConfig:
        async with sql.session() as session:
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
        async with sql.session() as session:
            session.add(config)
            await session.commit()
            await session.refresh(config)
