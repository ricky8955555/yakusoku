import asyncio

from sqlalchemy.exc import NoResultFound

from yakusoku.archive import group_manager, user_manager


async def main():
    for group in await group_manager.get_groups():
        for member in group.members:
            try:
                _ = await user_manager.get_user(member)
            except NoResultFound:
                await group_manager.remove_member(group.id, member)


asyncio.run(main())
