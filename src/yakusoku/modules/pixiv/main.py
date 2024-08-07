import html
import re
import traceback

from aiogram.dispatcher.event.bases import SkipHandler
from aiogram.filters.callback_data import CallbackData, CallbackQueryFilter
from aiogram.types import (
    BufferedInputFile,
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from yakusoku.context import module_manager

from . import api, ugoira
from .types import IllustType, XRestrict

_ARTWORK_URL_REGEX = re.compile(
    r"pixiv\.net/(?:[a-z]*/)?(?:artworks/|i/|member_illust\.php\?(?:[\w=&]*\&|)illust_id=)(\d+)",
    re.IGNORECASE,
)


router = module_manager.create_router()


class Download(CallbackData, prefix="pixiv_download"):
    id: int


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
        await reply.edit_text(f"上面返回了错误, 看不到图力. {html.escape(ex.message)}")
        raise
    except Exception as ex:
        await reply.edit_text(f"坏了, 出现了没预料到的错误! {html.escape(str(ex))}")
        raise
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
    buttons: list[list[InlineKeyboardButton]] = []
    if illust.x_restrict == XRestrict.NONE and illust.sl == 2:
        buttons.append(
            [InlineKeyboardButton(text="下载原图", callback_data=Download(id=id).pack())]
        )

        await reply.edit_text("下载预览图并发送中...")

        try:
            if illust.illust_type == IllustType.UGOIRA:
                meta = await api.illust_ugoira_meta(id)
                archive = await api.download_asset(meta.src)
                gif = ugoira.compose_ugoira_gif(archive, meta.frames)
                file = BufferedInputFile(gif, f"{id}.gif")
                message = await message.reply_animation(
                    file, caption=info, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            else:
                assert illust.urls.regular, "regular size url not found."
                photo = await api.download_asset(illust.urls.regular)
                file = BufferedInputFile(photo, f"{id}.jpg")
                message = await message.reply_photo(
                    file, info, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
                )
            await reply.delete()
            return message
        except Exception as ex:
            reason = "发送失败了"
            traceback.print_exc()
    else:
        reason = "为 R-18 / R-18G 类型或敏感内容"
    await reply.edit_text(
        info + f"\n由于插图{reason}, 没法展示出来 QwQ",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    return reply


@router.callback_query(CallbackQueryFilter(callback_data=Download))
async def download(query: CallbackQuery, callback_data: Download):
    if not isinstance(query.message, Message):
        return query.answer("消息太远古了, 我不是考古学家w")

    reply = await query.message.reply("请求数据中...")

    try:
        illust = await api.illust(callback_data.id)
    except Exception:
        await query.answer("请求出错了!")
        await reply.delete()
        raise

    await reply.edit_text("下载中...")

    try:
        if illust.illust_type == IllustType.UGOIRA:
            meta = await api.illust_ugoira_meta(callback_data.id)
            archive = await api.download_asset(meta.original_src)
            gif = ugoira.compose_ugoira_gif(archive, meta.frames)
            file = BufferedInputFile(gif, f"{callback_data.id}.gif")
        elif not illust.urls.original:
            await reply.delete()
            return await query.answer("坏了, 没有找到原图w")
        else:
            image = await api.download_asset(illust.urls.original)
            file = BufferedInputFile(image, f"{illust.id}.jpg")
    except Exception:
        await query.answer("下载失败捏xwx")
        raise

    await reply.edit_text("发送中...")

    try:
        await query.message.reply_document(file)
        await query.answer("发送成功")
    except Exception:
        await query.answer("发送失败了xwx")
        raise
    finally:
        await reply.delete()


@router.message
async def match_url(message: Message):
    if not message.text:
        return
    ids = find_illust_ids(message.text)
    for id in ids:
        await send_illust(message, id)
    raise SkipHandler
