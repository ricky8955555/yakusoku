import os
from typing import Any

import yaml

BASE_PATH = os.path.abspath("./config/")


def load_yaml(path: str) -> Any:
    if not os.path.exists(path):
        return None
    with open(path) as fp:
        return yaml.safe_load(fp)


class Config:
    @classmethod
    def load(cls, name: str):
        path = os.path.join(BASE_PATH, name + ".yml")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        return cls(**(data if (data := load_yaml(path)) else {}))
