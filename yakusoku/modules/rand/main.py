import random

from aiogram.types import Message

from yakusoku.context import module_manager

dp = module_manager.dispatcher()


@dp.message_handler(commands=["randobj"])
async def randobj(message: Message):
    if len(args := message.text.split()) < 3:
        return await message.reply(
            "戳啦, 正确用法为 `/randobj <对象1> <对象2> ... <对象N>`", parse_mode="Markdown"
        )
    choice = random.choice(args[1:])
    await message.reply(f"那么就 {choice} 吧!")
