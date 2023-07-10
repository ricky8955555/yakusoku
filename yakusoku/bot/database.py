import os

from sqlitedict import SqliteDict

DATA_PATH = os.path.abspath("./data/bot/")


def get(name: str, table: str) -> SqliteDict:
    return SqliteDict(os.path.join(DATA_PATH, name), table, autocommit=True)
