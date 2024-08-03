import asyncio
import os
import platform
import shutil
import sys
from datetime import datetime

import humanize
import psutil
from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from yakusoku import environ
from yakusoku.archive import group_manager, user_manager
from yakusoku.context import module_manager, sql
from yakusoku.dot.switch import switch_manager
from yakusoku.utils import exception

router = module_manager.create_router()


@router.message(Command("status"))
async def status(message: Message):
    process = psutil.Process()
    working_time = datetime.now() - datetime.fromtimestamp(process.create_time())

    process_memory = process.memory_info()
    memory = psutil.virtual_memory()

    # drop the first call.
    process.cpu_percent()
    await asyncio.sleep(1)

    process_info = (
        f"- 运行时间: {humanize.naturaldelta(working_time)}\n"
        f"- CPU 占用: {process.cpu_percent() / psutil.cpu_count():.1f}%\n"
        f"- 内存占用: {humanize.naturalsize(process_memory.rss)}"
        f" (总占比 {process_memory.rss / memory.total * 100:.1f}%)\n"
        f"- Python 版本: {'.'.join(map(str, sys.version_info[:3]))}"
    )

    group_count = len(await group_manager.get_groups())
    user_count = len(await user_manager.get_users())
    enabled_module_count = module_count = len(module_manager.loaded_modules)

    if message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        for module in module_manager.loaded_modules.values():
            config = await switch_manager.get_switch_config(message.chat.id, module.config)
            enabled_module_count -= not config.enabled

    database_size = os.path.getsize(sql.path)

    service_info = (
        f"- 模块: 已启用 {enabled_module_count} 个 / 共 {module_count} 个\n"
        f"- 群组数: {group_count}\n"
        f"- 用户信息缓存数: {user_count}\n"
        f"- 数据库大小: {humanize.naturalsize(database_size)}"
    )

    system = f"{platform.system()} {platform.processor()} {platform.release()}"
    os_release = exception.try_or_default(platform.freedesktop_os_release)
    if os_release and (os_name := os_release.get("NAME")):
        system = f"{os_name} ({system})"

    disk_usage = shutil.disk_usage(environ.working_dir)

    host_info = (
        f"- 系统: {system}\n"
        f"- CPU: {psutil.cpu_percent()}% ({psutil.cpu_count(False)} Core, {psutil.cpu_count(True)} Thread)\n"
        f"- 内存: {humanize.naturalsize(memory.used)} / {humanize.naturalsize(memory.total)}"
        f" ({memory.used / memory.total * 100:.1f}%)\n"
        f"- 硬盘 (工作目录): {humanize.naturalsize(disk_usage.used)} / {humanize.naturalsize(disk_usage.total)}"
        f" ({disk_usage.used / disk_usage.total * 100:.1f}%, {humanize.naturalsize(disk_usage.free)} 可用)\n"
        f"- 时间: {datetime.now().replace(microsecond=0)}"
    )

    await message.reply(
        f"进程信息:\n{process_info}\n\n服务信息:\n{service_info}\n\n宿主信息:\n{host_info}\n"
    )
