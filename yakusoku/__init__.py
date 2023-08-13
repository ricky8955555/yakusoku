import os

from yakusoku import constants
from yakusoku.config import Config
from yakusoku.database import SQLSessionManager


class BotConfig(Config):
    token: str
    owner: int
    skip_updates: bool = False


class CommonConfig(Config):
    # Capoo writing sticker
    writing_sticker: str = "CAACAgIAAxkBAAOpZLUxt3yp_ZiN40D4bJfh1GJbJ7MAAiMTAALo1uIScdlv0VTcu6UvBA"


bot_config = BotConfig.load("bot")
common_config = CommonConfig.load("common")

sql = SQLSessionManager(os.path.join(constants.DATA_PATH, "data.db"))
