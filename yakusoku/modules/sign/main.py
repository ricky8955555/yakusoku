from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatType, Message

from yakusoku.context import module_manager
from yakusoku.dot.sign import sign_manager
from yakusoku.filters import ManagerFilter

dp = module_manager.dispatcher()


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    ManagerFilter(),
    commands=["sign"],
)
async def sign(message: Message):
    config = await sign_manager.get_sign_config(message.chat.id)
    config.enabled = not config.enabled
    await sign_manager.update_sign_config(config)
    await message.reply("已经启用签名了捏w" if config.enabled else "已经停用签名了捏w")
