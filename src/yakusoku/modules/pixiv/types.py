from datetime import datetime
from enum import IntEnum
from typing import Generic, TypeVar

import pydantic.alias_generators
from pydantic import BaseModel, ConfigDict, Field

_T = TypeVar("_T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=pydantic.alias_generators.to_camel,
        populate_by_name=True,
        from_attributes=True,
    )


class AjaxResponse(BaseSchema, Generic[_T]):
    error: bool
    message: str
    body: _T | None


class XRestrict(IntEnum):
    NONE = 0
    R18 = 1
    R18G = 2


class IllustType(IntEnum):
    ILLUST = 0
    MANGA = 1
    UGOIRA = 2


class Urls(BaseSchema):
    mini: str | None = Field(alias="thumb_mini", default=None)
    thumb: str | None = Field(alias="thumb_mini", default=None)
    small: str | None = None
    regular: str | None = None
    original: str | None = None


class Tag(BaseSchema):
    tag: str
    locked: bool
    deletable: bool
    user_id: int | None = None
    user_name: str | None = None


class Tags(BaseSchema):
    author_id: int
    is_locked: bool
    tags: list[Tag]


class Frame(BaseSchema):
    file: str
    delay: int


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
    sl: int  # 2 - sfw ?
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


class UgoiraMeta(BaseSchema):
    src: str
    original_src: str
    mime_type: str = Field(alias="mime_type")
    frames: list[Frame]
