from dataclasses import dataclass

from ....common import config


@dataclass
class Config(config.Config):
    original_size: bool = False
