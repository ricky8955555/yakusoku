import asyncio
import lzma
import posixpath
from dataclasses import dataclass
from io import BytesIO, IOBase
from typing import AsyncIterable, Generator

from aiohttp import ClientSession

from ..types import Package
from . import PackageProvider, PackageRepository


@dataclass(frozen=True)
class AptSource:
    source: str
    suite: str
    arch: str

    def with_components(self, components: list[str]) -> list["AptComponent"]:
        return [AptComponent(self, component) for component in components]


@dataclass(frozen=True)
class AptComponent(PackageRepository):
    source: AptSource
    component: str

    @property
    def identifier(self) -> str:
        return f"{self.source.source.rstrip('/')}:{self.source.suite}:{self.source.arch}:{self.component}"

    def package_url(self, filename: str) -> str:
        return posixpath.join(self.source.source, filename)

    def packages_url(self) -> str:
        return posixpath.join(
            self.source.source,
            "dists",
            self.source.suite,
            self.component,
            f"binary-{self.source.arch}",
            "Packages.xz",
        )


class Apt(PackageProvider[AptComponent]):
    __scheme__ = "apt"

    def __init__(self) -> None:
        pass

    def _parse_fields(self, fields: dict[str, str], component: AptComponent) -> Package:
        return Package(
            repo=component.identifier,
            arch=fields["Architecture"],
            name=fields["Package"],
            description=fields["Description"],
            version=fields["Version"],
            url=component.package_url(fields["Filename"]),
        )

    @staticmethod
    def _read_fields(buffer: IOBase) -> dict[str, str]:
        fields = {}
        last_key = None

        while line := buffer.readline():
            line = line.decode()

            if line == "\n":
                break

            line = line.rstrip("\n")

            if line.startswith(" "):
                assert last_key, f"invalid data found. {line}"
                fields[last_key] += line
                continue

            data = line.split(":", 1)
            assert len(data) == 2, f"invalid data found. {line}"
            last_key, value = data[0], data[1].lstrip()
            fields[last_key] = value

        if not fields:
            raise EOFError

        return fields

    def _iter_packages(
        self, buffer: IOBase, component: AptComponent
    ) -> Generator[Package, None, None]:
        while True:
            try:
                fields = self._read_fields(buffer)
                yield self._parse_fields(fields, component)
            except EOFError:
                return

    async def fetch(self, repo: AptComponent) -> AsyncIterable[Package]:
        async with ClientSession() as session:
            async with session.get(repo.packages_url()) as response:
                response.raise_for_status()
                compressed = BytesIO(await response.read())

        with lzma.LZMAFile(compressed, format=lzma.FORMAT_XZ) as packages:
            for package in self._iter_packages(packages, repo):
                yield package
                await asyncio.sleep(0)
