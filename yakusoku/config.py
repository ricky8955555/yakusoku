import os

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as

from yakusoku.constants import CONFIG_PATH

os.makedirs(CONFIG_PATH, exist_ok=True)


class Config(BaseModel):
    @classmethod
    def load(cls, name: str):
        path = (
            path
            if os.path.exists(path := os.path.join(CONFIG_PATH, name + ".yaml"))
            else os.path.join(CONFIG_PATH, name + ".yml")
        )
        if os.path.exists(path):
            return parse_yaml_file_as(cls, path)
        return cls()
