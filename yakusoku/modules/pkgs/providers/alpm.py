import asyncio
import gzip
import posixpath
import tarfile
import tempfile
from dataclasses import dataclass
from io import BytesIO, IOBase
from pathlib import Path
from typing import AsyncGenerator, AsyncIterable, cast

from aiofile import TextFileWrapper, async_open
from aiohttp import ClientSession

from ..types import Package
from . import PackageProvider, PackageRepository


@dataclass(frozen=True)
class AlpmSource:
    source: str
    arch: str

    def with_repositories(self, repos: list[str]) -> list["AlpmRepository"]:
        return [AlpmRepository(self, repo) for repo in repos]


@dataclass(frozen=True)
class AlpmRepository(PackageRepository):
    source: AlpmSource
    repo: str

    @property
    def identifier(self) -> str:
        return f"{self.source.source.rstrip('/')}:{self.repo}:{self.source.arch}"

    def package_url(self, filename: str) -> str:
        return posixpath.join(
            self.source.source,
            self.repo,
            "os",
            self.source.arch,
            filename,
        )

    def db_url(self) -> str:
        return self.package_url(f"{self.repo}.db.tar.gz")


class Alpm(PackageProvider[AlpmRepository]):
    __scheme__ = "alpm"

    def __init__(self) -> None:
        pass

    def _parse_fields(self, fields: dict[str, str], repo: AlpmRepository) -> Package:
        return Package(
            repo=repo.identifier,
            name=fields["NAME"],
            arch=fields["ARCH"],
            version=fields["VERSION"],
            description=fields["DESC"],
            url=repo.package_url(fields["FILENAME"]),
        )

    @staticmethod
    async def _read_fields(afp: TextFileWrapper) -> dict[str, str]:
        key, value = None, ""
        fields = {}

        while True:
            line = await afp.readline()

            if not line:
                return fields

            if line == "\n" and key and value:
                fields[key] = value.rstrip("\n")
                key, value = None, ""
                continue

            if not key:
                key = line.rstrip("\n")
                # fmt: off
                assert (
                    key.startswith("%") and key.endswith("%")
                ), "key should starts and ends with '%'."
                # fmt: on
                key = key[1:-1]
            else:
                value += line

    async def _iter_packages(
        self, archive: IOBase, repo: AlpmRepository
    ) -> AsyncGenerator[Package, None]:
        with tempfile.TemporaryDirectory() as dir:
            dir = Path(dir)
            with tarfile.TarFile(fileobj=archive, mode="r") as tar:
                tar.extractall(dir)
            for package in dir.iterdir():
                async with async_open(package / "desc") as afp:
                    afp = cast(TextFileWrapper, afp)
                    fields = await self._read_fields(afp)
                    yield self._parse_fields(fields, repo)

    async def fetch(self, repo: AlpmRepository) -> AsyncIterable[Package]:
        async with ClientSession() as session:
            async with session.get(repo.db_url()) as response:
                response.raise_for_status()
                compressed = BytesIO(await response.read())

        with gzip.GzipFile(mode="r", fileobj=compressed) as archive:
            async for package in self._iter_packages(archive, repo):
                yield package
                await asyncio.sleep(0)
