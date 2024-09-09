import html
import time

from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

from yakusoku.context import module_manager

from .config import config
from .latex import render

router = module_manager.create_router()


@router.message(Command("latex"))
async def latex(message: Message, command: CommandObject):
    expression = command.args
    if not expression:
        return await message.reply("诶? 没给公式我渲染不了w")
    try:
        image = render(
            expression, math_fontfamily=config.math_fontfamily, format="png", dpi=config.dpi
        )
    except Exception as ex:
        return await message.reply(f"喵呜……渲染失败捏.\n{html.escape(str(ex))}")
    image = BufferedInputFile(image, f"latex_{time.time()}.png")
    try:
        await message.reply_photo(image)
    except TelegramBadRequest:
        await message.reply_document(image)
