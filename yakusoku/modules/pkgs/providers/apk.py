import asyncio
import gzip
import os
import posixpath
import tarfile
import tempfile
from dataclasses import dataclass
from io import BytesIO, IOBase
from typing import AsyncGenerator, AsyncIterable, cast

from aiofile import TextFileWrapper, async_open
from aiohttp import ClientSession

from ..types import Package
from . import PackageProvider, PackageRepository


@dataclass(frozen=True)
class ApkRepository(PackageRepository):
    source: str

    @property
    def identifier(self) -> str:
        return self.source
    
    def db_url(self) -> str:
        return posixpath.join(self.source, "APKINDEX.tar.gz")
    
    def package_url(self, name: str, version: str) -> str:
        return posixpath.join(self.source, f"{name}-{version}.apk")


class Apk(PackageProvider[ApkRepository]):
    __scheme__ = "alpm"

    def __init__(self) -> None:
        pass

    def _parse_fields(self, fields: dict[str, str], repo: ApkRepository) -> Package:
        return Package(
            repo=repo.identifier,
            name=fields["P"],
            arch=fields["A"],
            version=fields["V"],
            description=fields["T"],
            url=repo.package_url(fields["P"], fields["V"]),
        )

    @staticmethod
    async def _read_fields(afp: TextFileWrapper) -> dict[str, str]:
        fields = {}

        while True:
            line = await afp.readline()
            line = line.rstrip("\n")

            if not line:
                break

            data = line.split(":", 1)
            assert len(data) == 2, f"invalid data found. {line}"
            fields[data[0]] = data[1]

        if not fields:
            raise EOFError

        return fields

    async def _iter_packages(
        self, archive: IOBase, repo: ApkRepository
    ) -> AsyncGenerator[Package, None]:
        with tempfile.TemporaryDirectory() as dir:
            with tarfile.TarFile(fileobj=archive, mode="r") as tar:
                tar.extractall(dir)

            async with async_open(os.path.join(dir, "APKINDEX")) as afp:
                afp = cast(TextFileWrapper, afp)
                while True:
                    try:
                        fields = await self._read_fields(afp)
                        yield self._parse_fields(fields, repo)
                    except EOFError:
                        return

    async def fetch(self, repo: ApkRepository) -> AsyncIterable[Package]:
        async with ClientSession() as session:
            async with session.get(repo.db_url()) as response:
                response.raise_for_status()
                compressed = BytesIO(await response.read())

        with gzip.GzipFile(mode="r", fileobj=compressed) as archive:
            async for package in self._iter_packages(archive, repo):
                yield package
                await asyncio.sleep(0)
