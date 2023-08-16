import aiogram
from aiogram import Bot, Dispatcher

from yakusoku import bot_config, modules, sql


async def on_startup(_):
    await sql.init_db()
    await modules.register_commands()


async def on_shutdown(_):
    sql.close()


bot = Bot(bot_config.token)
dp = Dispatcher(bot)
dp.chat_member_handlers.once = False
dp.message_handlers.once = False
bot.disable_web_page_preview = True
bot.parse_mode = "HTML"

modules.load(dp)

aiogram.executor.start_polling(
    dp, skip_updates=bot_config.skip_updates, on_startup=on_startup, on_shutdown=on_shutdown
)
