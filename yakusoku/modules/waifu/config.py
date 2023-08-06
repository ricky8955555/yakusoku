from datetime import time

from yakusoku.config import Config


class WaifuConfig(Config):
    reset_time: time = time(0, 0)


config = WaifuConfig.load("waifu")
