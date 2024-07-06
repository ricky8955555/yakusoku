import os

from pydantic import BaseModel
from pydantic_yaml import parse_yaml_file_as

from yakusoku.environ import config_path

os.makedirs(config_path, exist_ok=True)


class Config(BaseModel):
    @classmethod
    def load(cls, name: str):
        path = (
            path
            if os.path.exists(path := os.path.join(config_path, name + ".yaml"))
            else os.path.join(config_path, name + ".yml")
        )
        if os.path.exists(path):
            return parse_yaml_file_as(cls, path)
        return cls()
