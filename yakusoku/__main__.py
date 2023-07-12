import asyncio
from dataclasses import dataclass

import aiogram
from aiogram import Bot, Dispatcher

from yakusoku import modules
from yakusoku.config import Config


@dataclass(frozen=True)
class BotConfig(Config):
    token: str
    skip_updates: bool = False


config = BotConfig.load("bot")

bot = Bot(config.token)
dp = Dispatcher(bot)
dp.chat_member_handlers.once = False
dp.message_handlers.once = False

loop = asyncio.new_event_loop()

modules.load(dp)
loop.run_until_complete(modules.register_commands())

aiogram.executor.start_polling(dp, skip_updates=config.skip_updates, loop=loop)
