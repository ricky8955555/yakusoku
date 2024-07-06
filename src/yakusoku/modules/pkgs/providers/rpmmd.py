import asyncio
import gzip
import posixpath
from dataclasses import dataclass
from io import BytesIO
from typing import AsyncIterable, BinaryIO, Generator, Iterator, cast
from xml.etree import ElementTree

import magic
import zstandard
from aiohttp import ClientSession

from ..types import Package
from . import PackageProvider, PackageRepository

_COMMON_NAMESPACE = "http://linux.duke.edu/metadata/common"
_REPO_NAMESPACE = "http://linux.duke.edu/metadata/repo"


@dataclass(frozen=True)
class RpmMdRepository(PackageRepository):
    source: str

    @property
    def identifier(self) -> str:
        return self.source

    def url(self, *paths: str) -> str:
        return posixpath.join(self.source, *paths)


class RpmMd(PackageProvider[RpmMdRepository]):
    __scheme__ = "rpm-md"

    def __init__(self) -> None:
        pass

    @staticmethod
    async def _find_primary_data_location(xml: BinaryIO) -> str:
        read = False
        for event, element in cast(
            Iterator[tuple[str, ElementTree.Element]], ElementTree.iterparse(xml, ["start", "end"])
        ):
            if (
                event == "start"
                and element.tag == f"{{{_REPO_NAMESPACE}}}data"
                and element.attrib["type"] == "primary"
            ):
                read = True
            if read and event == "end" and element.tag == f"{{{_REPO_NAMESPACE}}}data":
                break
            if read and element.tag == f"{{{_REPO_NAMESPACE}}}location":
                return element.attrib["href"]

        raise ValueError("primary data location not found.")

    def _parse_primary_data(
        self, xml: BinaryIO, repo: RpmMdRepository
    ) -> Generator[Package, None, None]:
        name, arch, version, summary, location = None, None, None, None, None

        for _, element in cast(
            Iterator[tuple[str, ElementTree.Element]], ElementTree.iterparse(xml)
        ):
            if element.tag == f"{{{_COMMON_NAMESPACE}}}name":
                name = element.text
            elif element.tag == f"{{{_COMMON_NAMESPACE}}}arch":
                arch = element.text
            elif element.tag == f"{{{_COMMON_NAMESPACE}}}version":
                version = f'{element.attrib["ver"]}-{element.attrib["rel"]}'
            elif element.tag == f"{{{_COMMON_NAMESPACE}}}summary":
                summary = element.text
            elif element.tag == f"{{{_COMMON_NAMESPACE}}}location":
                location = element.attrib["href"]
            elif element.tag == f"{{{_COMMON_NAMESPACE}}}package":
                assert (
                    name and arch and version and summary and location
                ), "some fields are missing."
                yield Package(
                    repo=repo.identifier,
                    name=name,
                    arch=arch,
                    version=version,
                    description=summary,
                    url=repo.url(location),
                )
                name, arch, version, summary, location = None, None, None, None, None
            elif element.tag == f"{{{_COMMON_NAMESPACE}}}metadata":
                return

            element.clear()  # clear the element to release memory

    async def _fetch_primary_data_location(self, repo: RpmMdRepository) -> str:
        url = repo.url("repodata", "repomd.xml")

        async with ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                xml = BytesIO(await response.read())

        location = await self._find_primary_data_location(xml)
        return location

    @staticmethod
    def _decompressor(file: BinaryIO, mime: str) -> BinaryIO:
        match mime:
            case "application/gzip":
                return cast(BinaryIO, gzip.GzipFile(fileobj=file, mode="r"))
            case "application/zstd":
                decompressor = zstandard.ZstdDecompressor()
                return decompressor.stream_reader(file)
            case _:
                raise ValueError(f"compression {mime} not supported.")

    async def fetch(self, repo: RpmMdRepository) -> AsyncIterable[Package]:
        location = await self._fetch_primary_data_location(repo)

        async with ClientSession() as session:
            async with session.get(repo.url(location)) as response:
                response.raise_for_status()
                data = BytesIO(await response.read())

        mime = magic.from_buffer(data.read(16), mime=True)
        data.seek(0)

        if mime != "text/xml":
            data = self._decompressor(data, mime)

        with data:
            for package in self._parse_primary_data(data, repo):
                yield package
                await asyncio.sleep(0)
