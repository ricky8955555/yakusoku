import urllib.parse
from typing import TypeVar

from aiohttp import ClientSession

from .types import AjaxResponse, Illust, IllustPage, UgoiraMeta

_T = TypeVar("_T")

_API = "https://www.pixiv.net/"
_PIXIV_CAT = "https://pixiv.cat"


class ApiError(Exception):
    message: str

    def __init__(self, message: str) -> None:
        self.message = message


def _extract_body(response: AjaxResponse[_T]) -> _T:
    if response.error or response.body is None:
        raise ApiError(response.message)
    return response.body


async def illust(id: int) -> Illust:
    async with ClientSession(_API) as session:
        async with session.get(f"/ajax/illust/{id}") as response:
            data = await response.read()
    response = AjaxResponse[Illust].model_validate_json(data)
    return _extract_body(response)


async def illust_pages(id: int) -> list[IllustPage]:
    async with ClientSession(_API) as session:
        async with session.get(f"/ajax/illust/{id}/pages") as response:
            data = await response.read()
    response = AjaxResponse[list[IllustPage]].model_validate_json(data)
    return _extract_body(response)


async def illust_ugoira_meta(id: int) -> UgoiraMeta:
    async with ClientSession(_API) as session:
        async with session.get(f"/ajax/illust/{id}/ugoira_meta") as response:
            data = await response.read()
    response = AjaxResponse[UgoiraMeta].model_validate_json(data)
    return _extract_body(response)


async def download_pximg(url: str, proxy: str | None = None) -> bytes:
    headers = {"Referer": _API} if proxy is None else {}
    if proxy:
        parsed = urllib.parse.urlparse(url)
        url = parsed._replace(netloc=proxy).geturl()

    async with ClientSession(headers=headers) as session:
        async with session.get(url) as response:
            return await response.read()


async def download_from_pixiv_cat(
    id: int, base: str | None = None, page: int | None = None
) -> bytes:
    base = base or _PIXIV_CAT
    filename = f"{id}-{page}.png" if page else f"{id}.png"
    url = urllib.parse.urljoin(base, filename)

    async with ClientSession() as session:
        async with session.get(url) as response:
            return await response.read()
