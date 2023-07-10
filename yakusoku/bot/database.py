import os
from typing import Any

from sqlitedict import SqliteDict

DATA_PATH = os.path.abspath("./data/bot/")

os.makedirs(DATA_PATH, exist_ok=True)


def get(name: str, table: str) -> Any:
    return SqliteDict(os.path.join(DATA_PATH, name), table, autocommit=True)
