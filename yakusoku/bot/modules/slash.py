import re

from aiogram.dispatcher.filters import Filter
from aiogram.types import Message

from . import dispatcher

dp = dispatcher()

PATTERN = re.compile(r"(?:\/\$([a-zA-Z0-9]+)|\/([^a-zA-Z0-9\s]+))\s*(.+)?")


class SlashFilter(Filter):
    async def check(self, message: Message) -> bool:  # type: ignore
        return not message.is_command() and message.text.startswith("/")


@dp.message_handler()
async def slash(message: Message):
    matches = PATTERN.match(message.text)
    if not matches or not (first := matches.group(1) or matches.group(2)):
        return
    second = matches.group(3)
    sender = message.sender_chat or message.from_user
    sender_mention: str = sender.get_mention(as_html=True)
    origin = message.reply_to_message or message
    target = origin.sender_chat or origin.from_user
    target_mention: str = target.get_mention(
        name="自己" if target.id == sender.id else None,
        as_html=True,
    )
    reply = (
        f"{sender_mention} {first} {target_mention} {second}!"
        if second
        else f"{sender_mention} {first}了 {target_mention}!"
    )
    await message.bot.send_message(message.chat.id, reply, parse_mode="HTML")
