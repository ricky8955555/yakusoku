import dataclasses
import random
import traceback
from dataclasses import dataclass

import aiohttp
from aiogram.types import Message

from yakusoku import config
from yakusoku.modules import command_handler

COUNTRIES_DATA_URL = (
    "https://raw.githubusercontent.com/zhaoweih/countries_json/master/countries.json"
)

DEFAULT_TYPES = ["男孩子", "女孩子", "正太", "萝莉", "喵喵", "汪!"]
FALLBACK_COUNTRIES = ["中国", "美国", "日本", "韩国", "印度", "韩国", "泰国", "英国", "马来西亚", "澳大利亚"]


@dataclass(frozen=True)
class Config(config.Config):
    custom_types: list[str] = dataclasses.field(default_factory=list)
    overwritten_types: bool = False
    custom_countries: list[str] = dataclasses.field(default_factory=list)
    overwritten_countries: bool = False


_config = Config.load("umnos")
_countries: list[str] = []


def get_types() -> list[str]:
    return (
        _config.custom_types if _config.overwritten_types else DEFAULT_TYPES + _config.custom_types
    )


async def get_countries() -> list[str]:
    global _countries
    if _config.overwritten_countries and _config.custom_countries:
        return _config.custom_countries
    if _countries:
        return _countries
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(COUNTRIES_DATA_URL) as response:
                countries = [
                    country["chinese"] for country in await response.json(content_type=None)
                ]
    except Exception:
        traceback.print_exc()
        return (
            _config.custom_countries
            if _config.overwritten_countries
            else FALLBACK_COUNTRIES + _config.custom_countries
        )
    countries += _config.custom_countries
    _countries = countries
    return countries


@command_handler(["umnos", "rebirth", "reborn"], "うみなおし 转生吧~")
async def umnos(message: Message):
    country = random.choice(await get_countries())
    type = random.choice(get_types())
    await message.reply(f"转生成功! 你现在是 {country} 的 {type} 了!")
