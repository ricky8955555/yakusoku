import aiohttp
from pydantic import BaseModel, Field

DEFAULT_API_URL = "https://v1.hitokoto.cn"

TYPES = {
    "a": "动画",
    "b": "漫画",
    "c": "游戏",
    "d": "文学",
    "e": "原创",
    "f": "来自网络",
    "g": "其他",
    "h": "影视",
    "i": "诗词",
    "j": "网易云",
    "k": "哲学",
    "l": "抖机灵",
}


class Sentence(BaseModel):
    id: int
    uuid: str
    hitokoto: str
    type: str
    source: str = Field(alias="from")
    from_who: str | None
    creator: str
    creator_uid: int
    reviewer: int
    commit_from: str
    created_at: int
    length: int


def get_type_desc(type: str) -> str:
    return TYPES.get(type, "未知")


async def hitokoto(params: dict[str, str] | None = None, api: str | None = None) -> Sentence:
    async with aiohttp.ClientSession() as session:
        async with session.get(api or DEFAULT_API_URL, params=params) as response:
            data = await response.read()
            return Sentence.model_validate_json(data)
