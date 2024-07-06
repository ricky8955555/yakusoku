from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.dot.switch import switch_manager
from yakusoku.filters import GroupFilter, ManagerFilter

router = module_manager.create_router()


@router.message(Command("switch"), GroupFilter, ManagerFilter)
async def switch(message: Message, command: CommandObject):
    if not (name := command.args):
        return await message.reply("戳啦, 正确用法为 `/switch <模块名称>`", parse_mode="Markdown")
    module = module_manager.loaded_modules.get(name)
    if not module:
        return await message.reply(f"没找到 {name} 模块捏w")
    if not module.config.can_disable:
        return await message.reply(f"这个模块不能动 QwQ")
    config = await switch_manager.get_switch_config(message.chat.id, module.config)
    config.enabled = not config.enabled
    await switch_manager.update_switch_config(config)
    await message.reply(
        f"已经启用 {name} 模块了捏w" if config.enabled else f"已经停用 {name} 模块了捏w"
    )
