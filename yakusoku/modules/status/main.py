import os
import platform
import sys
from datetime import datetime

import humanize
import psutil
from aiogram.types import Message

from yakusoku.context import sql, module_manager
from yakusoku.archive import group_manager, user_manager

dp = module_manager.dispatcher()


@dp.message_handler(commands=["status"])
async def status(message: Message):
    process = psutil.Process()
    working_time = datetime.now() - datetime.fromtimestamp(process.create_time())

    process_info = (
        f"- 运行时间: {humanize.naturaldelta(working_time)}\n"
        f"- CPU 占用: {process.cpu_percent()} %\n"
        f"- 内存占用: {humanize.naturalsize(process.memory_info().rss)}\n"
        f"- Python 版本: {sys.version.split(' ')[0]}"
    )

    group_count = len(await group_manager.get_groups())
    user_count = len(await user_manager.get_users())
    database_size = os.path.getsize(sql.path)

    service_info = (
        f"- 群组数: {group_count}\n"
        f"- 用户信息缓存数: {user_count}\n"
        f"- 数据库大小: {humanize.naturalsize(database_size)}"
    )

    memory = psutil.virtual_memory()

    host_info = (
        f"- 系统: {platform.system()} {platform.release()}\n"
        f"- CPU 占用: {psutil.cpu_percent()} %\n"
        f"- 内存: {humanize.naturalsize(memory.used)} / {humanize.naturalsize(memory.total)}"
    )

    await message.reply(
        f"进程信息:\n{process_info}\n\n服务信息:\n{service_info}\n\n宿主信息:\n{host_info}\n"
    )
