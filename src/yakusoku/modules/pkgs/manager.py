import os
from datetime import datetime
from typing import Generic

import aioshutil
from zakodb.core import ZakoDb
from zakodb.exc import NotAZakoDbError
from zakodb.query import Query
from zakodb.types import ZakoDbHashMethod, ZakoDbMetadata, ZakoDbType, ZakoDbTypedValue
from zakodb.utils import create_hashed_bytes

from yakusoku.utils.tempfile import TemporaryFile

from .providers import AnyPackageRepository as _T
from .providers import PackageProvider
from .types import Package


class NoSuchPackage(Exception):
    pass


class DatabaseUpdating(Exception):
    pass


class DatabaseIsEmpty(Exception):
    pass


class PackageManager(Generic[_T]):
    provider: PackageProvider[_T]
    repos: list[_T]
    path: str
    hash_method: ZakoDbHashMethod
    _db: ZakoDb | None
    _updating: bool

    def __init__(
        self,
        provider: PackageProvider[_T],
        repos: list[_T],
        path: str,
        hash_method: ZakoDbHashMethod,
    ) -> None:
        self.provider = provider
        self.repos = repos
        self.path = path
        self.hash_method = hash_method
        self._updating = False
        self._db = None
        self.reload()

    def reload(self) -> None:
        if self._db is None:
            self.close()

        self._db = None

        if not os.path.exists(self.path):
            return

        fp = open(self.path, "rb")

        try:
            self._db = ZakoDb.load(fp)
        except NotAZakoDbError:
            fp.close()

    def _check_updating(self) -> None:
        if self._updating:
            raise DatabaseUpdating

    @property
    def db(self) -> ZakoDb:
        if self._db is None:
            raise DatabaseIsEmpty
        return self._db

    @property
    def updating(self) -> bool:
        return self._updating

    def _create_metadata(self) -> ZakoDbMetadata:
        return ZakoDbMetadata(
            hash_method=self.hash_method,
            field_props=Package.__field_props__,
            extra_fields={
                "created_at": ZakoDbTypedValue(
                    type=ZakoDbType.FLOAT64, value=datetime.now().timestamp()
                )
            },
        )

    def close(self) -> None:
        if self._db is not None:
            self._db.io.close()

    def available(self) -> bool:
        return self._db is not None

    def info(self, name: str) -> Package:
        hashed_name = create_hashed_bytes(name.encode(Package.__encoding__), self.hash_method)

        PackageEntry = Query()
        entry = next(self.db.find_entry(PackageEntry.name == hashed_name), None)

        if entry is None:
            raise NoSuchPackage

        return Package.from_zakodb_entry(entry)

    async def search(self, name: str) -> list[Package]:
        PackageEntry = Query()

        entries = self.db.find_entry(PackageEntry.name.contains(name))
        results = list(map(Package.from_zakodb_entry, entries))

        return results

    async def _update_repo(self, writer: ZakoDb, repo: _T) -> None:
        async for package in self.provider.fetch(repo):
            writer.append_entry(package.to_zakodb_entry(writer.metadata.hash_method))

    async def _update_buffered(self) -> None:
        with TemporaryFile() as file:
            with open(file, "wb") as fp:
                writer = ZakoDb.create(fp, self._create_metadata())

                for repo in self.repos:
                    await self._update_repo(writer, repo)

            await aioshutil.move(file, self.path)

    async def update(self) -> None:
        self._check_updating()

        try:
            self._updating = True
            await self._update_buffered()
            self.reload()
        finally:
            self._updating = False

    def last_updated(self) -> datetime | None:
        if self._db is None:
            return None

        created_at = self._db.metadata.extra_fields.get("created_at")

        if created_at is None:
            return None

        if not isinstance(created_at.value, float):
            raise TypeError

        return datetime.fromtimestamp(created_at.value)

    async def clear(self) -> None:
        self._check_updating()

        # recreate an empty database
        self.close()
        os.remove(self.path)
        self._db = None
