import re

from aiogram.dispatcher.filters import Filter
from aiogram.types import Message

from ..utils import chat
from . import dispatcher

dp = dispatcher()

PATTERN = re.compile(r"\/(?:\$([a-zA-Z0-9]\S*)|\$?(\S+))\s*(.+)?")


class SlashFilter(Filter):
    async def check(self, message: Message) -> bool:  # type: ignore
        return message.text.startswith("/")


def get_reply(first: str, second: str, sender_mention: str, target_mention: str):
    if second:
        return f"{sender_mention} {first} {target_mention} {second} !"
    if first.endswith("了"):
        return f'{sender_mention} {first} {target_mention} !'
    return f'{sender_mention} {first}了 {target_mention} !'


@dp.message_handler(SlashFilter())
async def slash(message: Message):
    matches = PATTERN.match(message.text)
    if not matches or not (first := matches.group(1) or matches.group(2)):
        return
    second = matches.group(3)
    sender = message.sender_chat or message.from_user
    sender_mention: str = chat.get_mention_html(sender)
    origin = message.reply_to_message or message
    target = origin.sender_chat or origin.from_user
    target_mention: str = (  # type: ignore
        chat.get_mention_html(target, "自己")
        if target.id == sender.id
        else chat.get_mention_html(target)
    )
    reply = get_reply(first, second, sender_mention, target_mention)
    await message.bot.send_message(
        message.chat.id, reply, parse_mode="HTML", disable_web_page_preview=True
    )
