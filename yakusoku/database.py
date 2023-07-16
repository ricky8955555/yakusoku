import os
from typing import Any

from sqlitedict import SqliteDict

from yakusoku.constants import DATA_PATH

DATABASE_PATH = os.path.join(DATA_PATH, "database")
os.makedirs(DATA_PATH, exist_ok=True)


def get(name: str, table: str) -> Any:
    return SqliteDict(os.path.join(DATA_PATH, name + ".sqlite"), table, autocommit=True)
