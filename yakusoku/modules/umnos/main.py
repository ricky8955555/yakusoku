import random
import traceback

import aiohttp
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from yakusoku.config import Config
from yakusoku.context import module_manager
from yakusoku.filters import CallbackQueryFilter

COUNTRIES_DATA_URL = (
    "https://raw.githubusercontent.com/zhaoweih/countries_json/master/countries.json"
)

DEFAULT_TYPES = ["男孩子", "女孩子", "正太", "萝莉", "喵喵", "汪!"]
FALLBACK_COUNTRIES = ["中国", "美国", "日本", "韩国", "印度", "韩国", "泰国", "英国", "马来西亚", "澳大利亚"]


class UmnosConfig(Config):
    custom_types: list[str] = list()
    overwritten_types: bool = False
    custom_countries: list[str] = list()
    overwritten_countries: bool = False


dp = module_manager.dispatcher()

config = UmnosConfig.load("umnos")
countries: list[str] = []


def get_types() -> list[str]:
    return config.custom_types if config.overwritten_types else DEFAULT_TYPES + config.custom_types


async def get_countries() -> list[str]:
    global countries
    if config.overwritten_countries and config.custom_countries:
        return config.custom_countries
    if countries:
        return countries
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(COUNTRIES_DATA_URL) as response:
                countries = [
                    country["chinese"] for country in await response.json(content_type=None)
                ]
    except Exception:
        traceback.print_exc()
        return (
            config.custom_countries
            if config.overwritten_countries
            else FALLBACK_COUNTRIES + config.custom_countries
        )
    countries += config.custom_countries
    return countries


@dp.message_handler(commands=["umnos", "rebirth", "reborn"])
@dp.callback_query_handler(CallbackQueryFilter("umnos_refresh"))
async def umnos(update: Message | CallbackQuery):  # type: ignore
    if isinstance(update, CallbackQuery) and int(update.data.split(" ")[1]) != update.from_user.id:
        return await update.answer("不要帮别人转生捏!")
    country = random.choice(await get_countries())
    type = random.choice(get_types())
    reply = f"转生成功! 你现在是 {country} 的 {type} 了!"
    if isinstance(update, CallbackQuery):
        return await update.message.edit_text(reply, reply_markup=update.message.reply_markup)
    if update.sender_chat:
        return await update.reply(reply)
    buttons = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(  # type: ignore
                    text="继续转生!",
                    callback_data=f"umnos_refresh {update.from_user.id}",
                ),
            ]
        ]
    )
    return await update.reply(reply, reply_markup=buttons)
