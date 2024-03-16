from datetime import datetime

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatType, ContentTypes, Message
from cashews import Cache

from yakusoku.constants import FILTERED_IDS
from yakusoku.context import module_manager
from yakusoku.filters import NonAnonymousFilter
from yakusoku.utils import chat
from yakusoku.utils.exception import try_or_default_async

from . import basic, hitokoto
from .config import GreetingConfig
from .manager import GreetingManager

dp = module_manager.dispatcher()

cache = Cache()
cache.setup("mem://")

config = GreetingConfig.load("greeting")
manager = GreetingManager()

loaded = datetime.now()


@dp.message_handler(
    NonAnonymousFilter(),
    commands=["greet"],
)
async def switch_user_greeting(message: Message):
    data = await manager.get_greeting_data(message.from_id)
    data.enabled = not data.enabled
    await manager.update_greeting_data(data)
    await message.reply("问候功能启用啦! 以后会跟你问好的w" if data.enabled else "问候功能已经禁用啦! 以后不再打扰你了w")


async def greet(message: Message):
    adjusted = datetime.now() + config.timezone
    greeting = basic.basic_greeting(adjusted.time())
    sentence = await try_or_default_async(hitokoto.hitokoto, logging=True)
    sentence_content = (
        (
            f"{sentence.hitokoto}\n"
            + (
                f"—— {sentence.from_who} ({sentence.source})"
                if sentence.from_who
                else f"—— {sentence.source}"
            )
        )
        if sentence
        else ""
    )
    user = chat.get_mention_html(message.sender_chat or message.from_user)
    await message.reply(f"{greeting}! {user}.\n\n" f"{sentence_content}")


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    NonAnonymousFilter(),
    content_types=ContentTypes.all(),
)
@cache(ttl=config.check_ttl, key="user:{message.from_id}")
async def message_received(message: Message):
    data = await manager.get_greeting_data(message.from_id)
    cfg = await manager.get_greeting_config(message.chat.id)
    if message.from_id in FILTERED_IDS or not data.enabled or not cfg.enabled:
        return
    now = datetime.now()
    if now - loaded >= config.initial_trigger_span and (
        not data.last_message_time or now - data.last_message_time >= config.trigger_span
    ):
        await greet(message)
    data.last_message_time = datetime.now()
    await manager.update_greeting_data(data)
