import random

from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatType, Message

from yakusoku.archive import utils as archive_utils
from yakusoku.archive.exceptions import ChatDeleted
from yakusoku.modules import command_handler
from yakusoku.utils import chat


@command_handler(
    ["randmember"],
    "抽取幸运观众!",
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
)
async def randmember(message: Message):
    members = [
        member
        async for member in await archive_utils.get_user_members(message.chat.id)
        if member.id != message.from_id
    ]
    if not members:
        return await message.reply("目前群员信息不足捏, 等我熟悉一下群里环境? w")
    member = random.choice(members)
    try:
        member = await archive_utils.fetch_member(message.bot, message.chat.id, member.id)
    except ChatDeleted:
        return await message.reply("诶? 没抽到诶! 重新抽一下?")
    await message.reply(
        f"恭喜幸运观众 {archive_utils.user_mention_html(member)} "
        f"被 {chat.get_mention_html(message.from_user or message.sender_chat)} 抽中!",
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
