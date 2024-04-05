import contextlib
import re
import urllib.parse

from aiogram.types import Message

from yakusoku.context import module_manager

from . import api
from .types import IllustType, XRestrict

_ARTWORK_URL_REGEX = re.compile(r"pixiv\.net/artworks/(\d+)")


dp = module_manager.dispatcher()


def extract_illust_id(s: str) -> int:
    url = urllib.parse.urlparse(s.lower())
    if (
        url.scheme in ["http", "https", ""]
        and url.netloc in ["www.pixiv.net", "pixiv.net"]
        and len(parts := url.path.removeprefix("/").split("/")) == 2
        and parts[0] == "artworks"
    ):
        s = parts[1]
    with contextlib.suppress(ValueError):
        return int(s)
    raise ValueError("illust id is not found.")


def find_illust_ids(s: str) -> list[int]:
    return list(map(int, _ARTWORK_URL_REGEX.findall(s)))


def illust_type_description(type: IllustType) -> str:
    match type:
        case IllustType.ILLUST:
            return "插图"
        case IllustType.MANGA:
            return "漫画"


async def send_illust(message: Message, id: int) -> Message:
    try:
        illust = await api.illust(id)
    except api.ApiError as ex:
        return await message.reply(f"上面返回了错误, 看不到图力. {ex.message}")
    except Exception as ex:
        print(ex)
        return await message.reply(f"坏了, 出现了没预料到的错误! {ex}")
    illust.description = illust.description.replace("<br />", "\n")
    info = (
        f"<u><b>{illust.title}</b></u>\n\n"
        + f'ID: <a href="https://www.pixiv.net/artworks/{illust.id}">{illust.id}</a>\n'
        + (
            f"描述: \n<blockquote>{illust.description}</blockquote>\n"
            if 0 < len(illust.description) <= 100
            else ""
        )
        + f'作者: {illust.user_name} (<a href="https://www.pixiv.net/users/{illust.user_id}">{illust.user_account}</a>)\n'
        + f"类型: {illust_type_description(illust.illust_type)}\n"
        + f'标签: {", ".join(tag.tag for tag in illust.tags.tags)}\n'
        + f'限制类型: {"全年龄" if illust.x_restrict == XRestrict.NONE else illust.x_restrict.name}\n'
        + f"发布日期: {illust.create_date}\n"
        + f"更新日期: {illust.upload_date}\n"
    )
    if illust.x_restrict == XRestrict.NONE:
        try:
            assert illust.urls.original, "original url not found."
            photo = await api.download_illust(illust.urls.original)
            return await message.reply_photo(
                photo,
                info,
                inform=False,  # type: ignore
            )
        except Exception as ex:
            reason = "发送失败了"
            print(ex)
    else:
        reason = "为 R-18 / R-18G 类型"
    return await message.reply(
        info + f"\n由于插图{reason}, 没法展示出来 QwQ",
        inform=False,  # type: ignore
    )


@dp.message_handler(run_task=True)
async def match_url(message: Message):
    ids = find_illust_ids(message.text)
    for id in ids:
        await send_illust(message, id)


@dp.message_handler(commands="pixiv")
async def pixiv(message: Message):
    target = message.get_args()
    if not target:
        return await message.reply("没给目标我没办法找xwx")
    try:
        id = extract_illust_id(target)
    except ValueError:
        return await message.reply("看不懂捏w")
    return await send_illust(message, id)
