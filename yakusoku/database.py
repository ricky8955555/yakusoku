from __future__ import annotations

from sqlalchemy import MetaData, Table
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker


class SQLSessionManager:
    _engine: AsyncEngine
    _session: sessionmaker[AsyncSession]
    _path: str

    def __init__(self, path: str) -> None:
        self._path = path
        self._engine = create_async_engine("sqlite+aiosqlite:///" + path)
        self._session = sessionmaker(self._engine, class_=AsyncSession)

    @property
    def path(self) -> str:
        return self._path

    @property
    def engine(self) -> AsyncEngine:
        return self._engine

    @property
    def session(self) -> sessionmaker[AsyncSession]:
        return self._session

    async def init_db(self, metadata: MetaData) -> None:
        async with self._engine.begin() as conn:
            await conn.run_sync(metadata.create_all)

    async def init_db_with_tables(self, *tables: Table) -> None:
        async with self._engine.begin() as conn:
            for table in tables:
                await conn.run_sync(lambda engine: table.create(engine, True))  # type: ignore

    async def close(self) -> None:
        await self._engine.dispose()

    async def __aenter__(self) -> "SQLSessionManager":
        return self

    async def __aexit__(self, *_) -> None:
        await self.close()
