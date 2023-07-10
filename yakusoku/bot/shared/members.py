import contextlib

from aiogram.types import Chat, ChatMember

from .. import database

DATABASE_NAME = "members"
_db: dict[int, set[int]] = database.get(DATABASE_NAME, "members")


async def get_members(chat: Chat) -> set[ChatMember]:
    return {
        await chat.get_member(member) for member in get_member_ids(chat.id)
    }


def get_member_ids(chat_id: int) -> set[int]:
    return _db.get(chat_id) or set()


def clear_members(chat_id: int) -> None:
    _db[chat_id] = set()


# following code is strange
# due to there is some troubles while handling set in SqliteDict


def add_member_id(chat_id: int, member_id: int) -> None:
    if not (members := _db.get(chat_id)):
        members = set[int]()
    members.add(member_id)
    _db[chat_id] = members


def remove_member_id(chat_id: int, member_id: int) -> None:
    with contextlib.suppress(KeyError):
        members = _db[chat_id]
        members.remove(member_id)
        _db[chat_id] = members
