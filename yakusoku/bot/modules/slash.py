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
    sender: str = (message.sender_chat or message.from_user).get_mention(as_html=True)
    origin = message.reply_to_message or message
    target: str = (origin.sender_chat or origin.from_user).get_mention(name="自己", as_html=True)
    reply = f"{sender} {first} {target} {second}!" if second else f"{sender} {first}了 {target}!"
    await message.bot.send_message(message.chat.id, reply, parse_mode="HTML")
