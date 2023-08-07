import random

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatType, Message

from yakusoku.modules import command_handler
from yakusoku.shared import user_factory
from yakusoku.utils import chat


@command_handler(
    ["randmember"],
    "抽取幸运观众!",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def randmember(message: Message):
    members = [
        member
        for member in user_factory.get_user_members(message.chat.id)
        if member != message.from_id
    ]
    member = random.choice(members)
    user = await chat.get_chat(message.bot, member)
    await message.reply(
        f"恭喜幸运观众 {chat.get_mention_html(user)} "
        f"被 {chat.get_mention_html(message.from_user or message.sender_chat)} 抽中!",
        parse_mode="HTML",
    )


@command_handler(
    ["randobj"],
    "不知道干 (吃, ...) 什么? 抽!",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def randobj(message: Message):
    if len(args := message.text.split()) < 3:
        return await message.reply(
            "戳啦, 正确用法为 `/randobj <对象1> <对象2> ... <对象N>`", parse_mode="Markdown"
        )
    choice = random.choice(args[1:])
    await message.reply(f"那么就 {choice} 吧!")
