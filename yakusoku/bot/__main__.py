from dataclasses import dataclass

import aiogram
from aiogram import Bot, Dispatcher

from ..common.config import Config
from . import modules


@dataclass
class BotConfig(Config):
    token: str
    skip_updates: bool = False


config = BotConfig.load("bot/bot")

bot = Bot(config.token)
dp = Dispatcher(bot)
dp.message_handlers.once = False

modules.run(dp)
aiogram.executor.start_polling(dp, skip_updates=config.skip_updates)
