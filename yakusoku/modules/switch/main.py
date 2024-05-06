from aiogram.dispatcher.filters import ChatTypeFilter
from aiogram.types import ChatType, Message

from yakusoku.context import module_manager
from yakusoku.dot.switch import switch_manager
from yakusoku.filters import ManagerFilter

dp = module_manager.dispatcher()


@dp.message_handler(
    ChatTypeFilter([ChatType.GROUP, ChatType.SUPERGROUP]),  # type: ignore
    ManagerFilter(),
    commands=["switch"],
)
async def switch(message: Message):
    name = message.get_args()
    if not name:
        return await message.reply("戳啦, 正确用法为 `/switch <模块名称>`", parse_mode="Markdown")
    module = module_manager.loaded_modules.get(name)
    if not module:
        return await message.reply(f"没找到 {name} 模块捏w")
    if not module.config.can_disable:
        return await message.reply(f"这个模块不能动 QwQ")
    config = await switch_manager.get_switch_config(message.chat.id, module.config)
    config.enabled = not config.enabled
    await switch_manager.update_switch_config(config)
    await message.reply(f"已经启用 {name} 模块了捏w" if config.enabled else f"已经停用 {name} 模块了捏w")
