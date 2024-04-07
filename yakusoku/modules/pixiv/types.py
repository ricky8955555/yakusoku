from datetime import datetime
from enum import IntEnum
from typing import Any

import pydantic.utils
from pydantic import BaseModel, Field


class BaseSchema(BaseModel):
    class Config:
        alias_generator = pydantic.utils.to_lower_camel
        populate_by_name = True
        from_attributes = True


class AjaxResponse(BaseSchema):
    error: bool
    message: str
    body: Any | None


class XRestrict(IntEnum):
    NONE = 0
    R18 = 1
    R18G = 2


class IllustType(IntEnum):
    ILLUST = 0
    MANGA = 1
    UGOIRA = 2


class Urls(BaseSchema):
    mini: str | None = Field(alias="thumb_mini")
    thumb: str | None = Field(alias="thumb_mini")
    small: str | None
    regular: str | None
    original: str | None


class Tag(BaseSchema):
    tag: str
    locked: bool
    deletable: bool
    user_id: int | None
    user_name: str | None


class Tags(BaseSchema):
    author_id: int
    is_locked: bool
    tags: list[Tag]


class Illust(BaseSchema):
    # illust_id: int
    # illust_title: str
    # illust_comment: str
    id: int
    title: str
    description: str
    illust_type: IllustType
    create_date: datetime
    upload_date: datetime
    restrict: int  # ?
    x_restrict: XRestrict
    tags: Tags
    sl: int  # ?
    urls: Urls
    alt: str
    user_id: int
    user_name: str
    user_account: str
    # user_illusts: dict[str, "Illust"]


class IllustPage(BaseSchema):
    urls: Urls
    width: int
    height: int
