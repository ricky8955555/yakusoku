import contextlib
import html
import io
import re
import traceback
import urllib.parse

from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputFile,
    Message,
)

from yakusoku.context import module_manager
from yakusoku.filters import CallbackQueryFilter

from . import api, ugoira
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
        case IllustType.UGOIRA:
            return "动图"


async def send_illust(message: Message, id: int) -> Message:
    reply = await message.reply("请求中...")
    try:
        illust = await api.illust(id)
    except api.ApiError as ex:
        await message.reply(f"上面返回了错误, 看不到图力. {html.escape(ex.message)}")
        raise
    except Exception as ex:
        await message.reply(f"坏了, 出现了没预料到的错误! {html.escape(str(ex))}")
        raise
    finally:
        await reply.delete()
    illust.description = illust.description.replace("<br />", "\n")
    info = (
        f"<u><b>{illust.title}</b></u>\n\n"
        + f'ID: <a href="https://www.pixiv.net/artworks/{illust.id}">{illust.id}</a>\n'
        + (
            f"描述: \n<blockquote>{html.escape(illust.description)}</blockquote>\n"
            if 0 < len(illust.description) <= 100
            else ""
        )
        + f'作者: {html.escape(illust.user_name)} (<a href="https://www.pixiv.net/users/{illust.user_id}">{illust.user_account}</a>)\n'
        + f"类型: {illust_type_description(illust.illust_type)}\n"
        + f'标签: {", ".join(html.escape(tag.tag) for tag in illust.tags.tags)}\n'
        + f'限制类型: {"全年龄" if illust.x_restrict == XRestrict.NONE else illust.x_restrict.name}\n'
        + f"发布日期: {illust.create_date}\n"
        + f"更新日期: {illust.upload_date}\n"
    )
    buttons = []
    if illust.x_restrict == XRestrict.NONE:
        buttons.append(
            [
                InlineKeyboardButton(
                    "下载原图", callback_data=f"pixiv_download_illust:{id}"
                )  # type: ignore
            ]
        )

        reply = await message.reply("下载预览图并发送中...")

        try:
            if illust.illust_type == IllustType.UGOIRA:
                meta = await api.illust_ugoira_meta(id)
                archive = await api.download_asset(meta.src)
                gif = ugoira.compose_ugoira_gif(archive, meta.frames)
                stream = io.BytesIO(gif)
                file = InputFile(stream, f"{id}.gif")
                return await message.reply_animation(
                    file, caption=info, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            else:
                assert illust.urls.regular, "regular size url not found."
                photo = await api.download_asset(illust.urls.regular)
                return await message.reply_photo(
                    photo, info, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
        except Exception as ex:
            reason = "发送失败了"
            traceback.print_exc()
        finally:
            await reply.delete()
    else:
        reason = "为 R-18 / R-18G 类型"
    return await message.reply(
        info + f"\n由于插图{reason}, 没法展示出来 QwQ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@dp.callback_query_handler(CallbackQueryFilter("pixiv_download_illust"))
async def download_illust(query: CallbackQuery):  # type: ignore
    try:
        id = int(query.data.split(":")[1])
    except ValueError:
        return await query.answer("坏, 怎么来的非法请求!")

    reply = await query.message.reply("请求数据中...")

    try:
        illust = await api.illust(id)
    except Exception:
        await query.answer("请求出错了!")
        raise
    finally:
        await reply.delete()

    reply = await query.message.reply("下载中...")

    try:
        if illust.illust_type == IllustType.UGOIRA:
            meta = await api.illust_ugoira_meta(id)
            archive = await api.download_asset(meta.original_src)
            gif = ugoira.compose_ugoira_gif(archive, meta.frames)
            stream = io.BytesIO(gif)
            file = InputFile(stream, f"{id}.gif")
        elif not illust.urls.original:
            return await query.answer("坏了, 没有找到原图w")
        else:
            image = await api.download_asset(illust.urls.original)
            stream = io.BytesIO(image)
            file = InputFile(stream, f"{id}.jpg")
    except Exception:
        await query.answer("下载失败捏xwx")
        raise
    finally:
        await reply.delete()

    reply = await query.message.reply("发送中...")

    try:
        await query.message.reply_document(file)
    except Exception:
        await query.answer("发送失败了xwx")
        raise
    finally:
        await reply.delete()

    await query.answer()


@dp.message_handler(run_task=True)
async def match_url(message: Message):
    ids = find_illust_ids(message.text)
    for id in ids:
        await send_illust(message, id)


@dp.message_handler(commands=["pixiv"])
async def pixiv(message: Message):
    target = message.get_args()
    if not target:
        return await message.reply("没给目标我没办法找xwx")
    try:
        id = extract_illust_id(target)
    except ValueError:
        return await message.reply("看不懂捏w")
    return await send_illust(message, id)
