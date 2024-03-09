import random
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum, auto

import sqlmodel

from yakusoku import sql
from yakusoku.archive import utils as archive_utils

from .config import config
from .models import WAIFU_MAX_RARITY, WaifuConfig, WaifuData


class WaifuFetchState(Enum):
    NONE = auto()
    UPDATED = auto()
    RESTRICTED = auto()


@dataclass(frozen=True)
class WaifuFetchResult:
    waifu: int
    state: WaifuFetchState


class MemberNotEfficientError(Exception):
    pass


class NoChoosableWaifuError(Exception):
    pass


class WaifuManager:
    def __init__(self) -> None:
        pass

    async def get_waifu_data(self, group: int, member: int) -> WaifuData:
        async with sql.session() as session:
            statement = (
                sqlmodel.select(WaifuData)
                .where(WaifuData.group == group)
                .where(WaifuData.member == member)
            )
            results = await session.execute(statement)
            return (
                row[0] if (row := results.one_or_none()) else WaifuData(group=group, member=member)
            )

    async def get_waifu_config(self, user: int) -> WaifuConfig:
        async with sql.session() as session:
            statement = sqlmodel.select(WaifuConfig).where(WaifuConfig.user == user)
            results = await session.execute(statement)
            return row[0] if (row := results.one_or_none()) else WaifuConfig(user=user)

    async def update_waifu_data(self, data: WaifuData) -> None:
        async with sql.session() as session:
            session.add(data)
            await session.commit()
            await session.refresh(data)

    async def update_waifu_config(self, config: WaifuConfig) -> None:
        async with sql.session() as session:
            session.add(config)
            await session.commit()
            await session.refresh(config)

    async def _is_choosable(self, data: WaifuData) -> bool:
        return data.rarity < WAIFU_MAX_RARITY and not data.restricted

    async def _random_waifu(self, group: int, member: int) -> int:
        waifus = {
            waifu.id: data.get_weight()
            async for waifu in await archive_utils.get_user_members(group)
            if member != waifu.id
            and await self._is_choosable(data := await self.get_waifu_data(group, waifu.id))
        }
        try:
            return random.choices(list(waifus.keys()), list(waifus.values()), k=1)[0]
        except IndexError:
            raise MemberNotEfficientError
        except ValueError:
            raise NoChoosableWaifuError

    def _last_reset_time(self, query: datetime) -> datetime:
        return datetime.combine(
            query.date() - timedelta(days=query.time() < config.reset_time),
            config.reset_time,
        )

    async def _is_update_needed(self, data: WaifuData) -> bool:
        return not data.restricted and (
            not data.modified
            or data.modified <= self._last_reset_time(datetime.now())
            or not await self._is_choosable(data)
        )

    async def _update_waifu(self, group: int, member: int, waifu: int) -> None:
        data = await self.get_waifu_data(group, member)
        data.waifu = waifu
        data.modified = datetime.now()
        await self.update_waifu_data(data)

    async def fetch_waifu(self, group: int, member: int, force: bool = False) -> WaifuFetchResult:
        data = await self.get_waifu_data(group, member)
        if partner := data.get_partner():
            return WaifuFetchResult(partner, WaifuFetchState.RESTRICTED)
        if data.waifu and not await self._is_update_needed(data) and not force:
            return WaifuFetchResult(data.waifu, WaifuFetchState.NONE)

        waifu = await self._random_waifu(group, member)
        await self._update_waifu(group, member, waifu)
        return WaifuFetchResult(waifu, WaifuFetchState.UPDATED)

    async def get_waifu_datas(self, group: int) -> list[WaifuData]:
        async with sql.session() as session:
            statement = sqlmodel.select(WaifuData).where(WaifuData.group == group)
            results = await session.execute(statement)
            return [row[0] for row in results.all()]

    async def get_active_waifu_datas(self, group: int) -> list[WaifuData]:
        datas = await self.get_waifu_datas(group)
        return [data for data in datas if not await self._is_update_needed(data)]

    async def remove_waifu(self, group: int, member: int) -> None:
        async with sql.session() as session:
            statement = (
                sqlmodel.select(WaifuData)
                .where(WaifuData.group == group)
                .where(WaifuData.member == member)
            )
            results = await session.execute(statement)
            await session.delete(results.one()[0])
            await session.commit()

    async def remove_group(self, group: int) -> None:
        async with sql.session() as session:
            statement = sqlmodel.select(WaifuData).where(WaifuData.group == group)
            results = await session.execute(statement)
            for row in results.all():
                await session.delete(row)
            await session.commit()
