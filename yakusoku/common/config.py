import os
from typing import Any

import yaml

BASE_PATH = os.path.abspath("./config/")


def load_yaml(path: str) -> Any:
    with open(path) as fp:
        return yaml.safe_load(fp)


class Config:
    @classmethod
    def load(cls, name: str):
        return cls(**load_yaml(os.path.join(BASE_PATH, name + ".yml")))
