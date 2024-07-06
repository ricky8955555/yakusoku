import asyncio

from sqlalchemy.exc import NoResultFound

from yakusoku import context
from yakusoku.archive import group_manager, user_manager
from yakusoku.modules.waifu.manager import WaifuManager
from yakusoku.modules.waifu.registry import Registry as WaifuRegistry


async def main():
    for group in await group_manager.get_groups():
        for member in group.members:
            try:
                _ = await user_manager.get_user(member)
            except NoResultFound:
                await group_manager.remove_member(group.id, member)

        waifu_manager = WaifuManager(context.sql)
        waifu_registry = WaifuRegistry(waifu_manager)
        for waifu in await waifu_manager.get_waifu_datas(group.id):
            try:
                _ = await user_manager.get_user(waifu.member)
            except NoResultFound:
                if waifu.get_partner():
                    await waifu_registry.divorce(waifu.group, waifu.member)
                await waifu_manager.remove_waifu(waifu.group, waifu.member)


asyncio.run(main())
