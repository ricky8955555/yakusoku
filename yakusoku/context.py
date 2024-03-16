import os

from yakusoku import constants
from yakusoku.configs import BotConfig, CommonConfig
from yakusoku.database import SQLSessionManager
from yakusoku.module import ModuleManager

module_manager: ModuleManager

bot_config = BotConfig.load("bot")
common_config = CommonConfig.load("common")

sql = SQLSessionManager(os.path.join(constants.DATA_PATH, "data.db"))
