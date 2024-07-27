import html
import random
import re

from aiogram import F
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from yakusoku.archive import user_manager
from yakusoku.archive import utils as archive_utils
from yakusoku.archive.models import UserData
from yakusoku.context import module_manager
from yakusoku.utils import chat, exception

from . import process
from .config import config

router = module_manager.create_router()

PATTERN = re.compile(r"\/(?:[\$\/]([a-zA-Z0-9]\S*)|[\$\/]?([^a-zA-Z0-9\s]\S*))\s*(.*)")

FALLBACK_PRPR_VERBS = ["贴了贴", "prpr 了", "ペロペロ了", "舔了"]


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


@router.message(Command("prpr", ignore_mention=True))
async def prpr(message: Message, command: CommandObject):
    sender = message.sender_chat or message.from_user

    if sender is None:
        return

    target = None

    if reply_to := message.reply_to_message:
        target = reply_to.sender_chat or reply_to.from_user
    if command.mention:
        target = await exception.try_or_fallback_async(
            user_manager.get_user_from_username, command.mention
        )
    if target is None:
        target = sender

    if isinstance(target, str):
        target = f"@{target}"
    else:
        name = "自己" if target.id == sender.id else None
        if isinstance(target, UserData):
            target = archive_utils.user_mention_html(target, name)
        else:
            target = chat.mention_html(target, name)

    sender = chat.mention_html(sender)

    verbs = [] if config.overwritten_prpr_verbs else FALLBACK_PRPR_VERBS
    verbs += config.prpr_verbs

    verb = random.choice(verbs)
    reply = f"{sender} {verb} {target}"

    await message.reply(reply)
