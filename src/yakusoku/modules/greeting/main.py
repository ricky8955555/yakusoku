from datetime import datetime

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters import Command
from aiogram.types import Message
from cashews import Cache

from yakusoku.constants import FILTERED_IDS
from yakusoku.context import module_manager, sql
from yakusoku.filters import GroupFilter, NonAnonymousFilter
from yakusoku.utils import chat
from yakusoku.utils.exception import try_or_default_async

from . import basic, hitokoto
from .config import GreetingConfig
from .manager import GreetingManager

router = module_manager.create_router()

cache = Cache()
cache.setup("mem://")

config = GreetingConfig.load("greeting")
manager = GreetingManager(sql)

loaded = datetime.now()


@router.message(Command("greet"), NonAnonymousFilter, GroupFilter)
async def switch_user_greeting(message: Message):
    assert message.from_user
    data = await manager.get_greeting_data(message.from_user.id)
    data.enabled = not data.enabled
    await manager.update_greeting_data(data)
    await message.reply(
        "问候功能启用啦! 以后会跟你问好的w"
        if data.enabled
        else "问候功能已经禁用啦! 以后不再打扰你了w"
    )


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
    assert (user := message.sender_chat or message.from_user)
    user = chat.mention_html(user)
    await message.reply(f"{greeting}! {user}.\n\n" f"{sentence_content}")


@router.message(GroupFilter, NonAnonymousFilter)
@cache(ttl=config.check_ttl, key="user:{message.from_id}")
async def message_received(message: Message):
    assert message.from_user
    user_id = message.from_user.id
    if user_id in FILTERED_IDS:
        raise SkipHandler
    data = await manager.get_greeting_data(user_id)
    if not data.enabled:
        raise SkipHandler
    now = datetime.now()
    if now - loaded >= config.initial_trigger_span and (
        not data.last_message_time or now - data.last_message_time >= config.trigger_span
    ):
        await greet(message)
    data.last_message_time = datetime.now()
    await manager.update_greeting_data(data)
    raise SkipHandler
