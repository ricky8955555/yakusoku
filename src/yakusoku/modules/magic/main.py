import html
import traceback

import aiohttp
import magic
from aiogram import Bot
from aiogram.filters import Command, CommandObject
from aiogram.types import Downloadable, Message

from yakusoku.context import module_manager

router = module_manager.create_router()


def extract_file(message: Message) -> Downloadable | None:
    return (
        (message.photo[0] if message.photo else None)
        or message.animation
        or message.video
        or message.document
        or message.audio
        or message.voice
        or message.sticker
    )


async def get_file_type(bot: Bot, message: Message, mime: bool) -> str:
    file = extract_file(message)
    if not file:
        raise FileNotFoundError

    file = await bot.get_file(file.file_id)
    assert (path := file.file_path), "'file_path' should not be None."
    url = bot.session.api.file_url(bot.token, path)
    size = 512  # read 512 bytes only

    async with aiohttp.ClientSession(read_bufsize=size) as session:
        async with session.get(url) as request:
            request.raise_for_status()
            header = await request.content.read(size)

    return magic.from_buffer(header, mime)


@router.message(Command("magic", "mime"))
async def entry(message: Message, bot: Bot, command: CommandObject):
    analyzing = message.reply_to_message or message
    mime = command.command == "mime"

    try:
        typ = await get_file_type(bot, analyzing, mime)
    except FileNotFoundError:
        return await message.reply(
            f"诶? 没找到文件捏! 回复一条带文件的消息或者发送带 /{command} 指令的带文件消息再试试w"
        )
    except Exception as ex:
        traceback.print_exc()
        return await message.reply(f"aww 咱也不知道发生什么了w. {ex}")

    await message.reply(f"<code>{html.escape(typ)}</code>")
