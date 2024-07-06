from datetime import datetime

from sqlmodel import Field, SQLModel


class GreetingData(SQLModel, table=True):
    user: int = Field(primary_key=True)
    last_message_time: datetime | None = None
    enabled: bool = True
