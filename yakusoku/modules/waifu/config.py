from dataclasses import dataclass

from yakusoku import config


@dataclass(frozen=True)
class Config(config.Config):
    original_size: bool = False
