import aiogram
from aiogram import Bot, Dispatcher

from yakusoku import bot_config, modules


async def on_startup(_):
    await modules.register_commands()


bot = Bot(bot_config.token)
dp = Dispatcher(bot)
dp.chat_member_handlers.once = False
dp.message_handlers.once = False

modules.load(dp)

aiogram.executor.start_polling(dp, skip_updates=bot_config.skip_updates, on_startup=on_startup)
