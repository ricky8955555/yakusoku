from dataclasses import dataclass

from zakodb.types import (
    ZakoDbEntry,
    ZakoDbFieldProperty,
    ZakoDbHashedBytes,
    ZakoDbHashMethod,
    ZakoDbType,
)
from zakodb.utils import create_hashed_bytes


@dataclass(frozen=True, kw_only=True)
class Package:
    __encoding__ = "utf-8"

    __field_props__ = (
        ZakoDbFieldProperty(name="repo", type=ZakoDbType.BYTES),
        ZakoDbFieldProperty(name="name", type=ZakoDbType.HASHED_BYTES),
        ZakoDbFieldProperty(name="arch", type=ZakoDbType.BYTES),
        ZakoDbFieldProperty(name="version", type=ZakoDbType.BYTES),
        ZakoDbFieldProperty(name="description", type=ZakoDbType.BYTES),
        ZakoDbFieldProperty(name="url", type=ZakoDbType.BYTES),
    )

    repo: str
    name: str
    arch: str
    version: str
    description: str
    url: str

    def to_zakodb_entry(self, hash_method: ZakoDbHashMethod) -> ZakoDbEntry:
        return {
            "repo": self.repo.encode(self.__encoding__),
            "name": create_hashed_bytes(self.name.encode(self.__encoding__), hash_method),
            "arch": self.arch.encode(self.__encoding__),
            "version": self.version.encode(self.__encoding__),
            "description": self.description.encode(self.__encoding__),
            "url": self.url.encode(self.__encoding__),
        }

    @staticmethod
    def from_zakodb_entry(entry: ZakoDbEntry) -> "Package":
        if (
            not isinstance(repo := entry["repo"], bytes)
            or not isinstance(name := entry["name"], ZakoDbHashedBytes)
            or not isinstance(arch := entry["arch"], bytes)
            or not isinstance(version := entry["version"], bytes)
            or not isinstance(description := entry["description"], bytes)
            or not isinstance(url := entry["url"], bytes)
        ):
            raise TypeError

        return Package(
            repo=repo.decode(Package.__encoding__),
            name=name.content.decode(Package.__encoding__),
            arch=arch.decode(Package.__encoding__),
            version=version.decode(Package.__encoding__),
            description=description.decode(Package.__encoding__),
            url=url.decode(Package.__encoding__),
        )
