import html
import time
from io import BytesIO

from aiogram.types import InputFile, Message
from aiogram.utils.exceptions import PhotoDimensions

from yakusoku.context import module_manager

from .latex import render

dp = module_manager.dispatcher()


@dp.message_handler(commands=["latex"])
async def latex(message: Message):
    expression = message.get_args()
    if not expression:
        return await message.reply("诶? 没给公式我渲染不了w")
    try:
        image = render(expression, format="png", dpi=300)
    except Exception as ex:
        return await message.reply(f"喵呜……渲染失败捏.\n{html.escape(str(ex))}")
    try:
        await message.reply_photo(image)
    except PhotoDimensions as ex:
        file = InputFile(BytesIO(image), f"latex-{int(time.time())}.png")
        await message.reply_document(file)
