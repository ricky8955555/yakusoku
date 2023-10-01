from aiogram.types import Chat, ChatType, User
from sqlmodel import JSON, Column, Field, SQLModel


class GroupData(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    username: str | None
    members: list[int] = Field(default=[], sa_column=Column(JSON))

    @staticmethod
    def from_chat(chat: Chat) -> "GroupData":
        assert chat.type in [ChatType.GROUP, ChatType.SUPERGROUP], "chat is not a group"
        return GroupData(
            id=chat.id,
            name=chat.full_name,  # type: ignore
            username=chat.username,  # type: ignore
        )

    def update_from_chat(self, chat: Chat) -> None:
        assert chat.type in [ChatType.GROUP, ChatType.SUPERGROUP], "chat is not a group"
        self.id = chat.id
        self.name = chat.full_name
        self.username = chat.username  # type: ignore


class UserData(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    usernames: list[str] = Field(default=[], sa_column=Column(JSON))
    is_bot: bool = False

    @staticmethod
    def from_chat(chat: Chat) -> "UserData":
        assert chat.type == ChatType.PRIVATE, "chat is not a user"
        return UserData(
            id=chat.id,
            usernames=chat.active_usernames or [],  # type: ignore
        )

    def update_from_chat(self, chat: Chat) -> None:
        assert chat.type == ChatType.PRIVATE, "chat is not a user"
        self.id = chat.id
        self.usernames = chat.active_usernames or []  # type: ignore

    @staticmethod
    def from_user(user: User) -> "UserData":
        return UserData(
            id=user.id,
            name=user.full_name,
            usernames=[user.username] if user.username else [],
            is_bot=user.is_bot,
        )

    def update_from_user(self, user: User) -> None:
        self.id = user.id
        self.usernames = (
            self.usernames + ([user.username] if user.username not in self.usernames else [])
            if user.username
            else []
        )
        self.is_bot = user.is_bot
