import dataclasses
import random
import traceback

import aiohttp
from aiogram.types import Message

from yakusoku.config import Config
from yakusoku.modules import command_handler

COUNTRIES_DATA_URL = (
    "https://raw.githubusercontent.com/zhaoweih/countries_json/master/countries.json"
)

DEFAULT_TYPES = ["男孩子", "女孩子", "正太", "萝莉", "喵喵", "汪!"]
FALLBACK_COUNTRIES = ["中国", "美国", "日本", "韩国", "印度", "韩国", "泰国", "英国", "马来西亚", "澳大利亚"]


class UmnosConfig(Config):
    custom_types: list[str] = dataclasses.field(default_factory=list)
    overwritten_types: bool = False
    custom_countries: list[str] = dataclasses.field(default_factory=list)
    overwritten_countries: bool = False


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


@command_handler(["umnos", "rebirth", "reborn"], "うみなおし 转生吧~")
async def umnos(message: Message):
    country = random.choice(await get_countries())
    type = random.choice(get_types())
    await message.reply(f"转生成功! 你现在是 {country} 的 {type} 了!")
