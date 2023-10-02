import contextlib

from aiogram.types import Message

from yakusoku.archive import group_manager
from yakusoku.filters import OwnerFilter
from yakusoku.modules import command_handler


@command_handler(
    ["announce"],
    "大声公! (仅限机器人所有者)",
    OwnerFilter(),
)
async def announce(message: Message):
    if not (content := message.get_args()):
        return await message.reply("你又不说内容, 我怎么帮你通知 (恼")
    for group in await group_manager.get_groups():
        with contextlib.suppress(Exception):
            await message.bot.send_message(group.id, content)
    await message.reply("好了, 帮你通知完了w")
