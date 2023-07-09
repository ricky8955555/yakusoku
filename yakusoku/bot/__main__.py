from dataclasses import dataclass

from aiogram import Bot, Dispatcher
import aiogram

from . import modules
from ..common.config import Config


@dataclass
class BotConfig(Config):
    token: str
    skip_updates: bool = False


config = BotConfig.load("bot/bot")
bot = Bot(config.token)
dp = Dispatcher(bot)
modules.run(dp)
aiogram.executor.start_polling(
    dp, skip_updates=config.skip_updates
)
