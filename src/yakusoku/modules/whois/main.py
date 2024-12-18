import contextlib
import html
import traceback
from typing import Any, cast

import asyncwhois
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.utils.message import cut_message

from .config import config

router = module_manager.create_router()


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


@router.message(Command("whois"))
async def whois(message: Message, command: CommandObject):
    if not (target := command.args):
        return await message.reply("不给我目标我不造查什么w")

    try:
        entries = None

        if config.use_rdap:
            with contextlib.suppress(Exception):
                _, entries = await asyncwhois.aio_rdap(target)

        if entries is None:
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
