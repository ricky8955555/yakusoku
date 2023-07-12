import os
from typing import Any

import yaml

from yakusoku.constants import CONFIG_PATH

os.makedirs(CONFIG_PATH, exist_ok=True)


def load_yaml(path: str) -> Any:
    if not os.path.exists(path):
        return None
    with open(path) as fp:
        return yaml.safe_load(fp)


class Config:
    @classmethod
    def load(cls, name: str):
        path = os.path.join(CONFIG_PATH, name + ".yml")
        return cls(**(data if (data := load_yaml(path)) else {}))
