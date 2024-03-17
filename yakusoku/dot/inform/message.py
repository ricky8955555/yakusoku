from typing import Any, cast

from aiogram.types import ChatType, Message

from yakusoku.dot.patch import patch, patched
from yakusoku.utils import chat


@patch(Message)
class PatchedMessage:
    async def _process(self: Any, text: str, kwargs: dict[str, Any]) -> str:
        message = cast(Message, self)
        inform = kwargs.pop("inform", True)
        if not inform or message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return text
        mention = chat.get_mention_html(message.sender_chat or message.from_user)
        return f"{mention} {text}"

    @patched
    async def reply(self: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_reply(
            await PatchedMessage._process(self, text, kwargs), *args, **kwargs
        )

    @patched
    async def answer(self: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_answer(
            await PatchedMessage._process(self, text, kwargs), *args, **kwargs
        )

    @patched
    async def reply_photo(self: Any, photo: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_reply_photo(
            photo, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def answer_photo(self: Any, photo: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_answer_photo(
            photo, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def reply_audio(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_reply_audio(
            video, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def answer_audio(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_answer_audio(
            video, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def reply_document(
        self: Any, document: Any, caption: str, *args: Any, **kwargs: Any
    ) -> Any:
        return await self.__old_reply_document(
            document, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def answer_document(
        self: Any, document: Any, caption: str, *args: Any, **kwargs: Any
    ) -> Any:
        return await self.__old_answer_document(
            document, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def reply_video(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_reply_video(
            video, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def answer_video(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_answer_video(
            video, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def reply_voice(self: Any, voice: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_reply_voice(
            voice, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    async def answer_voice(self: Any, voice: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return await self.__old_answer_voice(
            voice, await PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )
