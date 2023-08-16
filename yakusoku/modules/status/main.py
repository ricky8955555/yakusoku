from datetime import datetime

import humanize
import psutil
from aiogram.types import Message

from yakusoku.archive import group_manager, user_manager
from yakusoku.modules import command_handler


@command_handler(["status"], "查看 Bot 状态")
async def status(message: Message):
    process = psutil.Process()

    working_time = datetime.now() - datetime.fromtimestamp(process.create_time())
    memory_usage = process.memory_info().rss
    cpu_percent = process.cpu_percent()

    process_info = (
        f"运行时间: {humanize.naturaldelta(working_time)}\n"
        f"内存占用: {humanize.naturalsize(memory_usage)}\n"
        f"CPU 占用: {cpu_percent * 100} %"
    )

    group_count = len(await group_manager.get_groups())
    user_count = len(await user_manager.get_users())

    service_info = f"群组数: {group_count}\n" f"用户信息缓存数: {user_count}"

    await message.reply(f"进程信息:\n{process_info}\n\n服务信息:\n{service_info}")
