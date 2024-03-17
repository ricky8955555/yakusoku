from typing import Any, cast

from aiogram.types import ChatType, Message, ParseMode

from yakusoku.dot.patch import patch, patched
from yakusoku.utils import chat


@patch(Message)
class PatchedMessage:
    def _process(self: Any, text: str, kwargs: dict[str, Any]) -> str:
        message = cast(Message, self)
        inform = kwargs.pop("inform", True)
        if not inform or message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]:
            return text
        parse_mode = kwargs.get("parse_mode") or message.bot.parse_mode
        if not parse_mode:
            kwargs["parse_mode"] = parse_mode = ParseMode.HTML
        as_html = cast(bool, parse_mode == ParseMode.HTML)
        mention = chat.get_mention(message.sender_chat or message.from_user, as_html=as_html)
        return f"{mention} {text}"

    @patched
    def reply(self: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_reply(PatchedMessage._process(self, text, kwargs), *args, **kwargs)

    @patched
    def answer(self: Any, text: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_answer(PatchedMessage._process(self, text, kwargs), *args, **kwargs)

    @patched
    def reply_photo(self: Any, photo: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_reply_photo(
            photo, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def answer_photo(self: Any, photo: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_answer_photo(
            photo, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def reply_audio(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_reply_audio(
            video, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def answer_audio(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_answer_audio(
            video, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def reply_document(self: Any, document: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_reply_document(
            document, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def answer_document(self: Any, document: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_answer_document(
            document, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def reply_video(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_reply_video(
            video, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def answer_video(self: Any, video: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_answer_video(
            video, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def reply_voice(self: Any, voice: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_reply_voice(
            voice, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )

    @patched
    def answer_voice(self: Any, voice: Any, caption: str, *args: Any, **kwargs: Any) -> Any:
        return self.__old_answer_voice(
            voice, PatchedMessage._process(self, caption, kwargs), *args, **kwargs
        )
