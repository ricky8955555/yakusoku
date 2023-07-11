import os
from typing import Any

from sqlitedict import SqliteDict

from .constants import DATA_PATH

os.makedirs(DATA_PATH, exist_ok=True)


def get(name: str, table: str) -> Any:
    return SqliteDict(os.path.join(DATA_PATH, name + ".sqlite"), table, autocommit=True)
