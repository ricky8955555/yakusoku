import random

from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from yakusoku.context import module_manager

router = module_manager.create_router()


@router.message(Command("randobj"))
async def randobj(message: Message):
    if not message.text or len(args := message.text.split()) < 3:
        return await message.reply(
            "戳啦, 正确用法为 `/randobj <对象1> <对象2> ... <对象N>`", parse_mode=ParseMode.MARKDOWN
        )
    choice = random.choice(args[1:])
    await message.reply(f"那么就 {choice} 吧!")
