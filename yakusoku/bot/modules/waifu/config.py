from dataclasses import dataclass

from ....common import config


@dataclass(frozen=True)
class Config(config.Config):
    original_size: bool = False
