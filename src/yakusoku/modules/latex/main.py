import html
import time

from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message

from yakusoku.context import module_manager

from .latex import render

router = module_manager.create_router()


@router.message(Command("latex"))
async def latex(message: Message, command: CommandObject):
    expression = command.args
    if not expression:
        return await message.reply("诶? 没给公式我渲染不了w")
    try:
        image = render(expression, format="png", routeri=300)
    except Exception as ex:
        return await message.reply(f"喵呜……渲染失败捏.\n{html.escape(str(ex))}")
    image = BufferedInputFile(image, f"latex_{time.time()}.png")
    await message.reply_photo(image)
