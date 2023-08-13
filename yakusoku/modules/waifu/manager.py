import random
from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, auto

import sqlmodel

from yakusoku import sql
from yakusoku.archive import user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.archive.models import UserData

from .config import config
from .models import WAIFU_MAX_RARITY, WaifuConfig, WaifuData


class WaifuFetchState(Enum):
    NONE = auto()
    UPDATED = auto()
    FORCED = auto()


@dataclass(frozen=True)
class WaifuFetchResult:
    waifu: UserData
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
        return data.rarity < WAIFU_MAX_RARITY and not data.forced

    async def _random_waifu(self, group: int, member: int) -> UserData:
        pairs = [
            (waifu, data)
            async for waifu in await archive_utils.get_user_members(group)
            if member != waifu.id
            and await self._is_choosable(data := await self.get_waifu_data(group, waifu.id))
        ]
        try:
            return random.choices(
                [pair[0] for pair in pairs], [pair[1].get_weight() for pair in pairs], k=1
            )[0]
        except IndexError:
            raise MemberNotEfficientError
        except ValueError:
            raise NoChoosableWaifuError

    async def _is_update_needed(self, data: WaifuData) -> bool:
        return not data.forced and (
            not data.modified
            or (
                datetime.now() >= datetime.combine(data.modified, config.reset_time)
                and data.modified <= datetime.combine(date.today(), config.reset_time)
            )
            or not await self._is_choosable(data)
        )

    async def _update_waifu(self, group: int, member: int, waifu: int) -> None:
        data = await self.get_waifu_data(group, member)
        data.waifu = waifu
        data.modified = datetime.now()
        await self.update_waifu_data(data)

    async def fetch_waifu(self, group: int, member: int, force: bool = False) -> WaifuFetchResult:
        if (data := await self.get_waifu_data(group, member)).forced:
            assert data.waifu, "no waifu when forced is true."
            waifu = await user_manager.get_user(data.waifu)
            return WaifuFetchResult(waifu, WaifuFetchState.FORCED)
        if data.waifu and not await self._is_update_needed(data) and not force:
            waifu = await user_manager.get_user(data.waifu)
            return WaifuFetchResult(waifu, WaifuFetchState.NONE)

        waifu = await self._random_waifu(group, member)
        await self._update_waifu(group, member, waifu.id)
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
            await session.delete(results.one())
            await session.commit()

    async def remove_group(self, group: int) -> None:
        async with sql.session() as session:
            statement = sqlmodel.select(WaifuData).where(WaifuData.group == group)
            results = await session.execute(statement)
            for rows in results.all():
                await session.delete(rows)
            await session.commit()
