import aiogram
from aiogram import Bot, Dispatcher

from yakusoku import context, environ
from yakusoku.module import ModuleManager


async def on_startup(_):
    await context.sql.init_db()
    await context.module_manager.register_commands()


async def on_shutdown(_):
    context.sql.close()


bot = Bot(context.bot_config.token)
dp = Dispatcher(bot)

dp.chat_member_handlers.once = False
dp.message_handlers.once = False
bot.disable_web_page_preview = True
bot.parse_mode = "HTML"

context.module_manager = module_manager = ModuleManager(dp)
module_manager.import_modules_from(environ.module_path)

aiogram.executor.start_polling(
    dp, skip_updates=context.bot_config.skip_updates, on_startup=on_startup, on_shutdown=on_shutdown
)
