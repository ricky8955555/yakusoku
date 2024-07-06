from aiogram.enums import ChatType
from aiogram.filters import Command
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.dot.switch import switch_manager
from yakusoku.utils.message import cut_message

router = module_manager.create_router()


@router.message(Command("help"))
async def help(message: Message):
    reply = ""
    group = message.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]
    for module in sorted(module_manager.loaded_modules.values(), key=lambda x: x.config.name):
        config = module.config
        if group:
            switch = await switch_manager.get_switch_config(message.chat.id, config)
            enabled = switch.enabled
        else:
            enabled = True
        if enabled:
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

    for part in cut_message(reply, "\n\n"):
        message = await message.reply(part)
