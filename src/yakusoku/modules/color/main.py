import io

import webcolors
from aiogram.filters import Command, CommandObject
from aiogram.types import BufferedInputFile, Message
from PIL import Image

from yakusoku.context import module_manager
from yakusoku.utils import exception

router = module_manager.create_router()


@router.message(Command("color"))
async def color(message: Message, command: CommandObject):
    inp = command.args
    if not inp:
        return await message.reply("没给我颜色捏w")
    inp = inp.strip()
    # fmt: off
    color = (
        exception.try_or_default(lambda: webcolors.hex_to_rgb(inp))
        or exception.try_or_default(lambda: webcolors.name_to_rgb(inp))
    )
    # fmt: on
    if color is None:
        return await message.reply("看不懂呜呜呜x")
    with Image.new("RGB", (128, 128), color) as im:
        imb = io.BytesIO()
        im.save(imb, "PNG")
    imb.seek(0)
    photo = BufferedInputFile(imb.read(), f"{inp}.png")
    name = exception.try_or_default(lambda: webcolors.rgb_to_name(color), "unnamed")
    hex = webcolors.rgb_to_hex(color)
    percent = webcolors.rgb_to_rgb_percent(color)
    await message.reply_photo(
        photo,
        f"""
名称 (Name): <code>{name}</code>
RGB: <code>{tuple(color)}</code>
十六进制 (Hex): <code>{hex}</code>
RGB 百分比 (RGB Percent): <code>{tuple(percent)}</code>
        """,
    )
