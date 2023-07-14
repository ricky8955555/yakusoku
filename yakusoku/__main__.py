from dataclasses import dataclass

import aiogram
from aiogram import Bot, Dispatcher

from yakusoku import modules
from yakusoku.config import Config


@dataclass(frozen=True)
class BotConfig(Config):
    token: str
    skip_updates: bool = False


async def on_startup(_):
    await modules.register_commands()


config = BotConfig.load("bot")

bot = Bot(config.token)
dp = Dispatcher(bot)
dp.chat_member_handlers.once = False
dp.message_handlers.once = False

modules.load(dp)

aiogram.executor.start_polling(dp, skip_updates=config.skip_updates, on_startup=on_startup)
