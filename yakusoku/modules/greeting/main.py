from datetime import datetime

from aiogram.types import ContentTypes, Message
from cashews import Cache

from yakusoku.modules import command_handler, dispatcher
from yakusoku.utils import chat
from yakusoku.utils.exception import try_or_default_async

from . import basic, hitokoto
from .config import ModuleConfig
from .manager import GreetingManager

dp = dispatcher()

cache = Cache()
cache.setup("mem://")

config = ModuleConfig.load("greeting")
manager = GreetingManager()

loaded = datetime.now()


@command_handler(["greet"], "启用/禁用问候功能")
async def switch_greeting(message: Message):
    data = await manager.get_greeting_data(message.from_id)
    data.enabled = not data.enabled
    await manager.update_greeting_data(data)
    await message.reply("问候功能已经禁用啦! 以后不再打扰你了w" if data.enabled else "问候功能启用啦! 以后会跟你问好的w")


async def greet(message: Message):
    greeting = basic.basic_greeting(datetime.now().time())
    sentence = await try_or_default_async(hitokoto.hitokoto, logging=True)
    # fmt: off
    sentence_content = (
        f"{sentence.hitokoto}\n"
        f"—— {sentence.from_who or '佚名'} ({sentence.source})"
    ) if sentence else ""
    await message.reply(
        f"{greeting}! {chat.get_mention_html(message.sender_chat or message.from_user)}.\n\n"
        f"{sentence_content}"
    )
    # fmt: on


@dp.message_handler(content_types=ContentTypes.all())
@cache(ttl=config.check_ttl, key="user:{message.from_id}")
async def message_received(message: Message):
    data = await manager.get_greeting_data(message.from_id)
    if not data.enabled:
        return
    now = datetime.now()
    if (
        (now - data.last_message_time >= config.trigger_span)
        if data.last_message_time
        else (now - loaded >= config.initial_trigger_span)
    ):
        await greet(message)
    data.last_message_time = datetime.now()
    await manager.update_greeting_data(data)
