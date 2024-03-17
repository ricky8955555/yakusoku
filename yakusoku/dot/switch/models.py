from sqlmodel import Field, SQLModel


class SwitchConfig(SQLModel, table=True):
    group: int = Field(primary_key=True)
    module: str = Field(primary_key=True)
    enabled: bool
