import abc
from typing import AsyncIterable, ClassVar, Generic, TypeVar

from ..types import Package


class PackageRepository(abc.ABC):
    @property
    @abc.abstractmethod
    def identifier(self) -> str: ...


AnyPackageRepository = TypeVar("AnyPackageRepository", bound=PackageRepository)


class PackageProvider(abc.ABC, Generic[AnyPackageRepository]):
    __scheme__: ClassVar[str] = NotImplemented

    @abc.abstractmethod
    def fetch(self, repo: AnyPackageRepository) -> AsyncIterable[Package]: ...
