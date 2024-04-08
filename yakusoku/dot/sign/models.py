from sqlmodel import Field, SQLModel


class SignConfig(SQLModel, table=True):
    group: int = Field(primary_key=True)
    enabled: bool = False
