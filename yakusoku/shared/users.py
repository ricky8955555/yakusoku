import contextlib

from yakusoku import database

DATABASE_NAME = "users"

_member_db: dict[int, set[int]] = database.get(DATABASE_NAME, "members")
_user_db: dict[str, int] = database.get(DATABASE_NAME, "users")


def get_members(chat: int) -> set[int]:
    return _member_db.get(chat) or set()


def delete_members(chat: int) -> None:
    with contextlib.suppress(KeyError):
        del _member_db[chat]


def get_user(username: str) -> int | None:
    return _user_db.get(username)


def update_user(username: str, user: int) -> None:
    _user_db[username] = user


# following code is strange
# due to there is some troubles while handling set in SqliteDict


def add_member(chat: int, member: int) -> None:
    members = _member_db.get(chat) or set()
    members.add(member)
    _member_db[chat] = members


def remove_member(chat: int, member: int) -> None:
    with contextlib.suppress(KeyError):
        members = _member_db[chat]
        members.remove(member)
        _member_db[chat] = members
