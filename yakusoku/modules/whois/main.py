import html
import traceback
from typing import Any, cast

import asyncwhois
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.utils.message import cut_message

dp = module_manager.dispatcher()


def stringify_entries(entries: dict[str, Any]) -> str:
    lines: list[str] = []

    for key, value in entries.items():
        if not value:
            continue
        key = " ".join(part.capitalize() for part in key.split("_"))
        if isinstance(value, list):
            value = cast(list[str], value)
            for item in value:
                lines.append(f"{key}: {item}")
        else:
            lines.append(f"{key}: {value}")

    return "\n".join(lines)


@dp.message_handler(commands=["whois"])
async def whois(message: Message):
    if not (target := message.get_args()):
        return await message.reply("不给我目标我不造查什么w")

    try:
        _, entries = await asyncwhois.aio_whois(target)
    except asyncwhois.NotFoundError:
        return await message.reply("诶? 这个东西找不到惹w")
    except Exception as ex:
        traceback.print_exc()
        return await message.reply(f"坏了, 我也不知道发生了甚么事. {ex}")

    entries = cast(dict[str, Any], entries)
    info = stringify_entries(entries)

    for part in cut_message(info):
        message = await message.reply(f"<code>{html.escape(part)}</code>")
