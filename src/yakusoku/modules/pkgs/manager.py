import os
from datetime import datetime
from typing import Generic

import aioshutil
import sqlmodel
from sqlalchemy.exc import OperationalError

from yakusoku.database import SQLSessionManager
from yakusoku.utils.tempfile import TemporaryFile

from .providers import AnyPackageRepository as _T
from .providers import PackageProvider
from .types import SQL_TABLES, Package


class NoSuchPackage(Exception):
    pass


class DatabaseUpdating(Exception):
    pass


class DatabaseIsEmpty(Exception):
    pass


class PackageManager(Generic[_T]):
    provider: PackageProvider[_T]
    repos: list[_T]
    _sql: SQLSessionManager
    _updating: bool

    def __init__(
        self,
        provider: PackageProvider[_T],
        repos: list[_T],
        database: str,
    ) -> None:
        self.provider = provider
        self.repos = repos
        self._sql = SQLSessionManager(database)
        self._updating = False

    async def _check_db(self) -> None:
        if await self.empty():
            raise DatabaseIsEmpty

    def _check_updating(self) -> None:
        if self._updating:
            raise DatabaseUpdating

    @property
    def sql(self) -> SQLSessionManager:
        return self._sql

    @property
    def updating(self) -> bool:
        return self._updating

    async def close(self) -> None:
        await self._sql.close()

    async def empty(self) -> bool:
        statement = sqlmodel.select(Package).limit(1)

        async with self._sql.session() as session:
            try:
                results = await session.execute(statement)
                return results.first() is None
            except OperationalError:
                return True

    async def info(self, name: str) -> Package:
        await self._check_db()

        statement = sqlmodel.select(Package).where(Package.name == name)

        async with self._sql.session() as session:
            results = await session.execute(statement)

        if not (row := results.first()):
            raise NoSuchPackage

        return row[0]

    async def search(self, name: str) -> list[Package]:
        await self._check_db()

        statement = sqlmodel.select(Package).where(
            Package.name.contains(name),  # type: ignore
        )

        async with self._sql.session() as session:
            results = await session.execute(statement)

        return [row[0] for row in results.all()]

    async def _update_repo_eager(self, writer: SQLSessionManager, repo: _T, commit_on: int) -> None:
        assert commit_on > 0, "commit_on should be a positive value."
        count = 0

        async with writer.session() as session:
            async for package in self.provider.fetch(repo):
                session.add(package)
                count += 1

                if count == commit_on:
                    await session.commit()
                    count = 0

            await session.commit()

    async def _update_repo_lazy(self, writer: SQLSessionManager, repo: _T) -> None:
        async with writer.session() as session:
            async for package in self.provider.fetch(repo):
                session.add(package)
            await session.commit()

    async def _update_repo(self, writer: SQLSessionManager, repo: _T, commit_on: int) -> None:
        if commit_on > 0:
            await self._update_repo_eager(writer, repo, commit_on)
        else:
            await self._update_repo_lazy(writer, repo)

    async def _update_buffered(self, commit_on: int) -> None:
        with TemporaryFile() as file:
            async with SQLSessionManager(file) as writer:
                await writer.init_db_with_tables(*SQL_TABLES)

                for repo in self.repos:
                    await self._update_repo(writer, repo, commit_on)

            await aioshutil.move(file, self._sql.path)

    async def update(self, commit_on: int = -1) -> None:
        self._check_updating()

        try:
            self._updating = True
            await self._update_buffered(commit_on)
        finally:
            self._updating = False

    async def last_updated(self) -> datetime | None:
        if await self.empty():
            return None

        stat = os.stat(self._sql.path)
        time = datetime.fromtimestamp(stat.st_mtime)
        return time

    async def clear(self) -> None:
        self._check_updating()

        # recreate an empty database
        await self._sql.close()
        path = self._sql.path
        os.remove(path)
        self._sql = SQLSessionManager(path)
