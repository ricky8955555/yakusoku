import abc
from collections import Counter
from datetime import timedelta
from typing import Any, ClassVar, Generic

from pydantic import BaseModel, validator

from yakusoku.config import Config

from .providers import AnyPackageRepository as _T
from .providers import PackageProvider
from .providers.alpm import Alpm, AlpmRepository, AlpmSource
from .providers.apk import Apk, ApkRepository
from .providers.apt import Apt, AptComponent, AptSource
from .providers.rpmmd import RpmMd, RpmMdRepository


class PkgDistroConfig(BaseModel, Generic[_T], abc.ABC):
    __scheme__: ClassVar[str] = NotImplemented
    __subtypes__: ClassVar[dict[str, type]] = {}

    name: str
    update: timedelta | None = None

    def __new__(cls, **kwargs: Any):
        scheme = kwargs.pop("scheme")
        typ = cls.__subtypes__.get(scheme)
        if not typ:
            raise ValueError(f"unknown scheme '{scheme}'.")
        obj = super().__new__(typ)
        typ.__init__(obj, **kwargs)
        return obj

    def __init_subclass__(cls):
        cls.__subtypes__[cls.__scheme__] = cls

    @abc.abstractmethod
    def to_instance(self) -> tuple[PackageProvider[_T], list[_T]]: ...


class PkgsConfig(Config):
    distros: list[PkgDistroConfig[Any]]
    max_jobs: int = 1
    retry_after: timedelta = timedelta(seconds=5)
    commit_on: int = 1000
    default_update: timedelta = timedelta(hours=4)

    @validator("distros")
    def distros_no_duplicate(cls, v: list[PkgDistroConfig[Any]]) -> list[PkgDistroConfig[Any]]:
        duplicate = [
            name for name, count in Counter(distro.name for distro in v).items() if count > 1
        ]
        assert not duplicate, f"duplicate distro found: {duplicate}."
        return v


class AptConfig(PkgDistroConfig[AptComponent]):
    __scheme__ = "apt"

    src: str
    suite: str
    arch: str
    with_noarch: bool = False
    comps: list[str]

    def to_instance(self) -> tuple[Apt, list[AptComponent]]:
        source = AptSource(self.src, self.suite, self.arch)
        comps = source.with_components(self.comps)
        if self.with_noarch:
            source = AptSource(self.src, self.suite, "all")
            comps.extend(source.with_components(self.comps))
        return Apt(), comps


class AlpmConfig(PkgDistroConfig[AlpmRepository]):
    __scheme__ = "alpm"

    src: str
    arch: str
    repos: list[str]

    def to_instance(self) -> tuple[Alpm, list[AlpmRepository]]:
        source = AlpmSource(self.src, self.arch)
        return Alpm(), source.with_repositories(self.repos)


class RpmMdConfig(PkgDistroConfig[RpmMdRepository]):
    __scheme__ = "rpm-md"

    repos: list[str]

    def to_instance(self) -> tuple[RpmMd, list[RpmMdRepository]]:
        return RpmMd(), list(map(RpmMdRepository, self.repos))


class ApkConfig(PkgDistroConfig[ApkRepository]):
    __scheme__ = "apk"

    repos: list[str]

    def to_instance(self) -> tuple[Apk, list[ApkRepository]]:
        return Apk(), list(map(ApkRepository, self.repos))
