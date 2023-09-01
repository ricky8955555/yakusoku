import asyncio
import dataclasses
import os
from dataclasses import dataclass
from datetime import datetime

from aiogram import Bot
from sqlitedict import SqliteDict

from yakusoku import bot_config, sql
from yakusoku.archive import group_manager, user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.archive.exceptions import ChatDeleted, ChatNotFound
from yakusoku.archive.models import UserData
from yakusoku.constants import DATA_PATH
from yakusoku.modules.waifu.manager import WaifuManager
from yakusoku.modules.waifu.models import WAIFU_DEFAULT_RARITY, WaifuConfig, WaifuData

OLD_DATABASE_PATH = os.path.join(DATA_PATH, "database")


@dataclass
class OldUserInfo:
    avatar: tuple[str | None, int] | None = None
    name: str | None = None
    usernames: set[str] = dataclasses.field(default_factory=set)
    is_user: bool = True


@dataclass(frozen=True)
class OldWaifuData:
    member: int
    last: int


@dataclass(frozen=True)
class OldWaifuGlobalProperty:
    mentionable: bool = False


@dataclass(frozen=True)
class OldWaifuLocalProperty:
    rarity: int = WAIFU_DEFAULT_RARITY
    married: int | None = None
    mentionable: bool | None = None


async def migrate_users(bot: Bot):
    old_db = SqliteDict(os.path.join(OLD_DATABASE_PATH, "user.sqlite"), "info")
    for id, info in old_db.items():
        id = int(id)  # type: ignore
        if id < 0:
            print(f"ignored invalid user id {id}")
        info = OldUserInfo(*info)  # type: ignore
        if info.name is not None:
            user = UserData(
                id=int(id), name=info.name, usernames=list(info.usernames), is_bot=not info.is_user
            )
            await user_manager.update_user(user)
            print(f"user {id} was migrated from local info. {user=}")
            continue
        print(f"user {id} with unknown name, trying to fetch info from server...")
        try:
            user = await archive_utils.fetch_user(bot, id)
            print(f"user {id} was migrated from server. {user=}")
        except ChatNotFound and ChatDeleted:
            print(f"unable to get info of user {id}, skipped.")


async def migrate_groups(bot: Bot):
    old_db = SqliteDict(os.path.join(OLD_DATABASE_PATH, "user.sqlite"), "members")
    for id, members in old_db.items():
        id = int(id)  # type: ignore
        if id > 0:
            print(f"ignored invalid group id {id}")
        print(f"trying to fetch group {id} info from server...")
        try:
            group = await archive_utils.fetch_group(bot, id)
        except ChatNotFound and ChatDeleted:
            print(f"unable to get info of group {id}, skipped.")
            continue
        group.members = list(members)  # type: ignore
        await group_manager.update_group(group)
        print(f"group {id} was migrated. {group=}")


async def migrate_waifus():
    groups = await group_manager.get_groups()
    old_waifu_db_path = os.path.join(OLD_DATABASE_PATH, "waifu.sqlite")
    manager = WaifuManager()
    for group in groups:
        print(f"migrating waifu datas from group {group.id}...")
        old_datas = SqliteDict(old_waifu_db_path, f"waifu_{group.id}")
        old_local_props = SqliteDict(old_waifu_db_path, f"property_{group.id}")
        for id, old_data in old_datas.items():
            print(f"migrating waifu {id} data from group {group.id}...")
            id = int(id)  # type: ignore
            if id < 0:
                print(f"ignored invalid waifu id {id}")
            old_data = OldWaifuData(*old_data)  # type: ignore
            props = (
                OldWaifuLocalProperty(*props)  # type: ignore
                if (props := old_local_props.get(id))
                else OldWaifuLocalProperty()
            )
            data = WaifuData(
                group=group.id,
                member=id,
                waifu=props.married or old_data.member,
                modified=datetime.fromtimestamp(old_data.last),
                forced=props.married is not None,
                rarity=props.rarity,
            )
            await manager.update_waifu_data(data)
            print(f"waifu {id} data from group {group.id} was migrated. {data=}")
        print(f"waifu datas from group {group.id} was migrated.")
    old_global_props = SqliteDict(old_waifu_db_path, "property")
    print("migrating waifu configs...")
    for id, props in old_global_props.items():
        id = int(id)  # type: ignore
        props = OldWaifuGlobalProperty(*props)  # type: ignore
        config = WaifuConfig(user=id, mentionable=props.mentionable)
        await manager.update_waifu_config(config)
        print(f"waifu {id} config was migrated. {config=}")


async def main():
    print("initializing database...")
    await sql.init_db()
    print("database was initialized.")
    bot = Bot(bot_config.token)
    print("migrating users...")
    await migrate_users(bot)
    print("users migrated.")
    print("migrating groups...")
    await migrate_groups(bot)
    print("groups migrated.")
    print("migrating waifus...")
    await migrate_waifus()
    print("waifus migrated.")


asyncio.run(main())
