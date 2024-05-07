import html
import inspect
from typing import Any, cast

from aiogram.types import CallbackQuery, ChatType, Message, ParseMode
from aiogram.utils import markdown

from yakusoku.dot.patch import patch, patched
from yakusoku.dot.sign import sign_manager
from yakusoku.utils import chat


@patch(Message)
class PatchedMessage:
    async def _handle(
        self: Any, raw: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Message:
        message = cast(Message, self)
        message: Message = getattr(message, "_original_message", None) or message
        if (
            message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP]
            or not (await sign_manager.get_sign_config(message.chat.id)).enabled
        ):
            return await raw(*args, **kwargs)

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

        from_callback_query: CallbackQuery | None = getattr(self, "_from_callback_query", None)
        sender = (
            from_callback_query.from_user
            if from_callback_query
            else message.sender_chat or message.from_user
        )

        as_html = cast(bool, parse_mode == ParseMode.HTML)
        mention = chat.get_mention(sender, as_html=as_html)

        trigger = from_callback_query.data if from_callback_query else message.text

        if as_html:
            trigger = f"<code>{html.escape(trigger)}</code>"
        else:
            trigger = f"`{markdown.escape_md(trigger)}`"

        info = f"{mention} 触发了 {trigger}"

        if (text := kwargs.get(text_param) or "") or len(args) <= text_index:
            kwargs[text_param] = f"{info}\n\n{text}"
        else:
            modified_args[text_index] = f"{info}\n\n{args[text_index]}"

        sent = await raw(*modified_args, **kwargs)
        setattr(sent, "_original_message", message)
        return sent

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
