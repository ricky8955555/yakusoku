import html
import re

from aiogram.dispatcher.filters import Filter
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.utils import chat

dp = module_manager.dispatcher()

PATTERN = re.compile(r"\/(?:\$([a-zA-Z0-9]\S*)|\$?([^a-zA-Z0-9\s]\S*))\s*(.*)")


class SlashFilter(Filter):
    async def check(self, message: Message) -> bool:  # type: ignore
        return message.text.startswith("/")


def get_reply(first: str, second: str, sender: str, target: str) -> str:
    if second:
        return f"{sender} {first} {target} {second} !"
    if "了" in first:
        return f"{sender} {first} {target} !"
    return f"{sender} {first}了 {target} !"


@dp.message_handler(SlashFilter())
async def slash(message: Message):
    matches = PATTERN.match(message.text)
    if not matches or not (first := matches.group(1) or matches.group(2)):
        return
    second = matches.group(3)
    sender = message.sender_chat or message.from_user
    sender_mention: str = chat.get_mention(sender)
    origin = message.reply_to_message or message
    target = origin.sender_chat or origin.from_user
    target_mention: str = chat.get_mention(target, "自己" if target.id == sender.id else None)
    reply = get_reply(html.escape(first), html.escape(second), sender_mention, target_mention)
    await message.reply(reply, inform=False)  # type: ignore
