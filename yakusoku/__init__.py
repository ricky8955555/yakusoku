from dataclasses import dataclass

from yakusoku.config import Config


@dataclass(frozen=True)
class BotConfig(Config):
    token: str
    owner: int
    skip_updates: bool = False


bot_config = BotConfig.load("bot")
