from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatType, Message

from yakusoku.context import module_manager
from yakusoku.dot.switch import switch_manager

dp = module_manager.dispatcher()


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    commands=["help"],
)
async def help(message: Message):
    reply = ""
    for module in sorted(module_manager.loaded_modules.values(), key=lambda x: x.config.name):
        config = module.config
        switch = await switch_manager.get_switch_config(message.chat.id, config)
        if switch.enabled:
            reply += f"<u><b>=== {config.name} ({config.description}) ===</b></u>\n"
            if config.commands:
                reply += "\n".join(
                    f"/{command} - {description}"
                    for command, description in config.commands.items()
                )
            else:
                reply += "<i>(无可用指令)</i>"
        else:
            reply += (
                f"<u><del><b>=== {config.name} ({config.description}) ===</b></del></u>\n"
                "<i>(已禁用)</i>"
            )
        reply += "\n\n"
    reply = reply.rstrip()
    await message.reply(reply, inform=False)  # type: ignore
