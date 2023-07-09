from dataclasses import dataclass

from aiogram import Bot, Dispatcher  # type: ignore
import aiogram

from . import modules
from ..common.config import Config


@dataclass
class BotConfig(Config):
    token: str


config = BotConfig.load("bot/bot")
bot = Bot(config.token)
dp = Dispatcher(bot)
modules.run(dp)
aiogram.executor.start_polling(dp, skip_updates=True)
