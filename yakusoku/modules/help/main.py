from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatType, Message

from yakusoku.context import module_manager

dp = module_manager.dispatcher()


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    commands=["help"],
)
async def help(message: Message):
    reply = ""
    for module in module_manager.loaded_modules:
        config = module.config
        if not config.commands:
            continue
        reply += f"<u><b>=== {config.name} ({config.description}) ===</b></u>\n"
        reply += "\n".join(
            f"/{command} - {description}" for command, description in config.commands.items()
        )
        reply += "\n\n"
    reply = reply.rstrip()
    await message.reply(reply, inform=False)  # type: ignore
