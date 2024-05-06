from typing import ClassVar

from sqlalchemy import Table
from sqlmodel import Field, SQLModel


class Package(SQLModel, table=True):
    __table__: ClassVar[Table]

    id: int | None = Field(default=None, primary_key=True)
    repo: str
    name: str
    arch: str
    version: str
    description: str
    url: str


SQL_TABLES = [Package.__table__]

for table in SQL_TABLES:
    SQLModel.metadata.remove(table)
