import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlmodel import SQLModel

from yakusoku import context
from yakusoku import dot as dot
from yakusoku import environ
from yakusoku.module import ModuleManager


async def main() -> None:
    default = DefaultBotProperties(
        parse_mode=ParseMode.HTML,
        link_preview_is_disabled=True,
    )

    bot = Bot(context.bot_config.token, default=default)
    dispatcher = Dispatcher()

    context.module_manager = module_manager = ModuleManager(dispatcher)
    module_manager.import_modules_from(environ.module_path)

    await context.sql.init_db(SQLModel.metadata)
    await module_manager.register_commands(bot)

    await dispatcher.start_polling(bot)

    await context.sql.close()


asyncio.run(main())
