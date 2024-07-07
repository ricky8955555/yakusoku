import html
import re

from aiogram import F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.utils import chat

from . import process

router = module_manager.create_router()

PATTERN = re.compile(r"\/(?:\$([a-zA-Z0-9]\S*)|\$?([^a-zA-Z0-9\s]\S*))\s*(.*)")


@router.message(F.text.startswith("/"))
async def slash(message: Message):
    if not message.text:
        raise SkipHandler
    matches = PATTERN.match(message.text)
    if not matches or not (first := matches.group(1) or matches.group(2)):
        raise SkipHandler
    second = matches.group(3)
    assert (sender := message.sender_chat or message.from_user)
    sender_mention: str = chat.mention_html(sender)
    origin = message.reply_to_message or message
    assert (target := origin.sender_chat or origin.from_user)
    target_mention: str = chat.mention_html(target, "自己" if target.id == sender.id else None)

    if second:
        first = html.escape(process.normalize_string(first))
        second = html.escape(process.normalize_string(second))
        reply = f"{sender_mention} {first} {target_mention} {second} !"
    else:
        first = html.escape(process.normalize_string(process.complete_ul(first)))
        reply = f"{sender_mention} {first} {target_mention} !"

    await message.reply(reply)
