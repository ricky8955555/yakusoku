import contextlib
import os
from concurrent.futures import Executor
from tempfile import mkstemp
from typing import Any

from aiofile import FileIOWrapperBase, async_open
from caio.asyncio_base import AsyncioContextBase


class TemporaryFile:
    _fd: int
    _path: str

    def __init__(
        self,
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | None = None,
    ) -> None:
        self._fd, self._path = mkstemp(suffix, prefix, dir)

    @property
    def path(self) -> str:
        return self._path

    @property
    def descriptor(self) -> int:
        return self._fd

    def __enter__(self) -> str:
        return self._path

    def close(self) -> None:
        with contextlib.suppress(Exception):
            os.close(self._fd)
        with contextlib.suppress(Exception):
            os.remove(self._path)

    def __exit__(self, *_: Any) -> None:
        self.close()


class TemporaryAioFile:
    _fd: int
    _path: str
    _fp: FileIOWrapperBase

    def __init__(
        self,
        mode: str = "r",
        encoding: str = "utf-8",
        context: AsyncioContextBase | None = None,
        executor: Executor | None = None,
        suffix: str | None = None,
        prefix: str | None = None,
        dir: str | None = None,
    ) -> None:
        self._fd, self._path = mkstemp(suffix, prefix, dir)
        self._fp = async_open(
            self._path, mode, encoding=encoding, context=context, executor=executor
        )

    async def __aenter__(self) -> FileIOWrapperBase:
        await self._fp.__aenter__()
        return self._fp

    async def __aexit__(self, *args: Any, **kwargs: Any) -> None:
        await self._fp.__aexit__(*args, **kwargs)

        with contextlib.suppress(Exception):
            os.close(self._fd)
        with contextlib.suppress(Exception):
            os.remove(self._path)
