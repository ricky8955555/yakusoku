from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel


class SQLSessionManager:
    _engine: AsyncEngine
    _session: sessionmaker[AsyncSession]

    def __init__(self, path: str) -> None:
        self._engine = create_async_engine("sqlite+aiosqlite:///" + path)
        self._session = sessionmaker(self._engine, class_=AsyncSession)

    @property
    def session(self) -> sessionmaker[AsyncSession]:
        return self._session

    async def init_db(self) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

    def close(self) -> None:
        self._session.close_all()
