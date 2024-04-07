import inspect
from typing import Any, cast

from aiogram.types import ChatType, Message, ParseMode

from yakusoku.dot.patch import patch, patched
from yakusoku.utils import chat


@patch(Message)
class PatchedMessage:
    def _handle(self: Any, raw: Any, args: tuple[Any, ...], kwargs: dict[str, Any]) -> str:
        message = cast(Message, self)
        inform = kwargs.pop("inform", True)
        if (
            not inform
            or message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]
            or message.from_user.id == message.bot.id
        ):
            return raw(*args, **kwargs)

        sig = inspect.signature(raw)
        params = list(sig.parameters.keys())

        modified_args = list(args)

        parse_mode_index = params.index("parse_mode")
        text_index, text_param = next(
            (index, param) for index, param in enumerate(params) if param in ["text", "caption"]
        )

        if not (parse_mode := kwargs.get("parse_mode")):
            if len(args) > parse_mode_index:
                modified_args[parse_mode_index] = parse_mode = (
                    args[parse_mode_index] or ParseMode.HTML
                )
            else:
                kwargs["parse_mode"] = parse_mode = ParseMode.HTML

        as_html = cast(bool, parse_mode == ParseMode.HTML)
        mention = chat.get_mention(message.sender_chat or message.from_user, as_html=as_html)

        if (text := kwargs.get(text_param) or "") or len(args) <= text_index:
            kwargs[text_param] = mention + text
        else:
            modified_args[text_index] = mention + args[text_index]

        return raw(*args, **kwargs)

    @patched
    def reply(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_reply, args, kwargs)

    @patched
    def answer(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_answer, args, kwargs)

    @patched
    def reply_photo(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_reply_photo, args, kwargs)

    @patched
    def answer_photo(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_answer_photo, args, kwargs)

    @patched
    def reply_audio(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_reply_audio, args, kwargs)

    @patched
    def answer_audio(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_answer_audio, args, kwargs)

    @patched
    def reply_document(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_reply_document, args, kwargs)

    @patched
    def answer_document(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_answer_document, args, kwargs)

    @patched
    def reply_video(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_reply_video, args, kwargs)

    @patched
    def answer_video(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_answer_video, args, kwargs)

    @patched
    def reply_voice(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_reply_voice, args, kwargs)

    @patched
    def answer_voice(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_answer_voice, args, kwargs)

    @patched
    def reply_animation(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_reply_animation, args, kwargs)

    @patched
    def answer_animation(self: Any, *args: Any, **kwargs: Any) -> Any:
        return PatchedMessage._handle(self, self.__old_answer_animation, args, kwargs)
