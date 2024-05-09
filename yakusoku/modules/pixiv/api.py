from typing import TypeVar

from aiohttp import ClientSession
from pydantic import BaseModel

from .types import AjaxResponse, Illust, IllustPage, UgoiraMeta

_T = TypeVar("_T", bound=BaseModel)

_API = "https://www.pixiv.net/"


class ApiError(Exception):
    message: str

    def __init__(self, message: str) -> None:
        self.message = message


class _IllustPages(BaseModel):
    __root__: list[IllustPage]


def _extract_body(type: type[_T], response: AjaxResponse) -> _T:
    if response.error or response.body is None:
        raise ApiError(response.message)
    return type.parse_obj(response.body)


async def illust(id: int) -> Illust:
    async with ClientSession(_API) as session:
        async with session.get(f"/ajax/illust/{id}") as response:
            data = await response.read()
    response = AjaxResponse.parse_raw(data)
    return _extract_body(Illust, response)


async def illust_pages(id: int) -> list[IllustPage]:
    async with ClientSession(_API) as session:
        async with session.get(f"/ajax/illust/{id}/pages") as response:
            data = await response.read()
    response = AjaxResponse.parse_raw(data)
    return _extract_body(_IllustPages, response).__root__


async def illust_ugoira_meta(id: int) -> UgoiraMeta:
    async with ClientSession(_API) as session:
        async with session.get(f"/ajax/illust/{id}/ugoira_meta") as response:
            data = await response.read()
    response = AjaxResponse.parse_raw(data)
    return _extract_body(UgoiraMeta, response)


async def download_asset(url: str) -> bytes:
    async with ClientSession(headers={"Referer": _API}) as session:
        async with session.get(url) as response:
            return await response.read()
