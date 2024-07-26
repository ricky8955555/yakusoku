import asyncio
import collections
import html
import logging
import os
import traceback
from datetime import datetime
from typing import Any

import humanize
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.environ import data_path
from yakusoku.utils.message import cut_message

from .config import PkgDistroConfig, PkgsConfig, SupportedDistros
from .manager import DatabaseIsEmpty, NoSuchPackage, PackageManager
from .providers import AnyPackageRepository as _T

router = module_manager.create_router()

config = PkgsConfig.load("pkgs")

base_path = data_path / "pkgs"
base_path.mkdir(exist_ok=True)

semaphore = asyncio.Semaphore(config.max_jobs)

logger = logging.getLogger()


def create_package_manager(config: PkgDistroConfig[_T]) -> PackageManager[_T]:
    provider, distros = config.to_instance()
    database = (base_path / f"{config.name}.db").as_posix()
    return PackageManager(provider, distros, database)


managers: dict[str, PackageManager[Any]] = {
    distro.name: create_package_manager(distro) for distro in config.distros
}


async def update_task(distro: SupportedDistros) -> None:
    manager = managers[distro.name]
    last = await manager.last_updated()
    cycle = distro.update or config.default_update
    retry_after = config.retry_after.total_seconds()

    if last and (datetime.now() - last) < cycle:
        remaining = last + cycle - datetime.now()
        await asyncio.sleep(remaining.total_seconds())

    while True:
        async with semaphore:
            try:
                logger.info(f"updating {distro.name} distro...")
                await manager.update(config.commit_on)
                logger.info(f"{distro.name} distro updated successfully.")
            except Exception:
                traceback.print_exc()
                if retry_after > 0:
                    logger.warning(f"{distro.name} update failed. retry after {retry_after}s.")
                    await asyncio.sleep(retry_after)
                    continue
                logger.error(f"{distro.name} update failed.")

        await asyncio.sleep(cycle.total_seconds())


update_tasks: list[asyncio.Task[None]] = []


@router.startup()
async def on_startup():
    update_tasks.extend(asyncio.create_task(update_task(distro)) for distro in config.distros)


@router.shutdown()
async def on_shutdown():
    for manager in managers.values():
        await manager.close()
    for task in update_tasks:
        task.cancel()


async def pkgs_all(message: Message, name: str):
    results: dict[str, str] = {}
    constructing: list[str] = []
    updating: list[str] = []

    for distro, manager in managers.items():
        try:
            package = await manager.info(name)
            info = f"{package.name}-{package.version}"
            if manager.updating:
                updating.append(distro)
                info += "*"
            results[distro] = info
        except NoSuchPackage:
            pass
        except DatabaseIsEmpty:
            constructing.append(distro)

    if not results and not constructing:
        return await message.reply("找不到捏")

    replies: list[str] = []

    if results:
        replies.append("\n".join(f"{distro}: {result}" for distro, result in results.items()))
    else:
        replies.append("找不到捏xwx")

    if constructing:
        replies.append("目前正在进行初始化的发行版有: " + ", ".join(constructing))

    if updating:
        replies.append("目前正在更新软件源的发行版有: " + ", ".join(updating))

    await message.reply("\n\n".join(replies))


async def pkgs_distro(message: Message, distro: str, name: str):
    result = next(
        ((cur, manager) for cur, manager in managers.items() if cur.startswith(distro)),
        None,
    )

    if not result:
        return await message.reply("这是什么发行版, 不认识捏~")

    target, manager = result

    try:
        package = await manager.info(name)
    except NoSuchPackage:
        return await message.reply("没有这样的包啦x")
    except DatabaseIsEmpty:
        return await message.reply("等一下嘛, 数据库第一次用还在找数据呢w")

    info = (
        f"<u><b>{html.escape(package.name)}</b></u>\n"
        f"<blockquote>{html.escape(package.description)}</blockquote>\n\n"
        f"・发行版: {html.escape(target)}\n"
        f"・版本: {html.escape(package.version)}\n"
        f"・架构: {html.escape(package.arch)}\n"
        f"・仓库: {html.escape(package.repo)}\n"
        f"・软件包下载地址: {html.escape(package.url)}\n"
    )

    await message.reply(info)


@router.message(Command("pkgs"))
async def pkgs(message: Message, command: CommandObject):
    if not (args := command.args):
        return await pkgs_help(message)

    args = args.split()
    length = len(args)

    if length == 1:
        return await pkgs_all(message, *args)
    if length == 2:
        return await pkgs_distro(message, *args)


async def pkgs_help(message: Message):
    distros = collections.defaultdict[str, list[str]](list)

    for distro in config.distros:
        distros[distro.scheme].append(distro.name)

    info = "\n".join(
        f"- {scheme}: " + ", ".join(f"{name}" for name in names)
        for scheme, names in distros.items()
    )
    usage = (
        "- <code>/pkgs</code> - 显示该帮助菜单\n"
        "- <code>/pkgs [软件包]</code> - 搜索各发行版软件包版本\n"
        "- <code>/pkgs [发行版] [软件包]</code> - 查询软件包在指定发行版的详细信息"
    )

    await message.reply(f"使用方法:\n{usage}\n\n目前可用的发行版:\n{info}")


@router.message(Command("pkgst"))
async def pkgs_status(message: Message):
    infos = [
        f"{name}:\n"
        f"数据库大小: {humanize.naturalsize(os.path.getsize(manager.sql.path))}\n"
        f"上次更新: {humanize.naturaltime(last)}\n"
        for name, manager in managers.items()
        if (last := await manager.last_updated()) is not None
    ]

    reply = "\n".join(infos)

    for part in cut_message(reply, "\n\n"):
        message = await message.reply(part)
