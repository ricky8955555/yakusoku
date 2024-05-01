import os

from yakusoku import environ
from yakusoku.configs import BotConfig, CommonConfig
from yakusoku.database import SQLSessionManager
from yakusoku.module import ModuleManager

module_manager: ModuleManager

bot_config = BotConfig.load("bot")
common_config = CommonConfig.load("common")

sql = SQLSessionManager(os.path.join(environ.data_path, "data.db"))
