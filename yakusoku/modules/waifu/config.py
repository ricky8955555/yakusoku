from datetime import time

from yakusoku.config import Config


class ModuleConfig(Config):
    reset_time: time = time(0, 0)


config = ModuleConfig.load("waifu")
