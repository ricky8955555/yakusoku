from dataclasses import dataclass

from ... import config


@dataclass(frozen=True)
class Config(config.Config):
    original_size: bool = False
