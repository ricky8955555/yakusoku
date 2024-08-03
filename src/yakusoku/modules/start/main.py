from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import Message

from yakusoku import constants
from yakusoku.context import module_manager

router = module_manager.create_router()


@router.message(Command("start"))
async def start(message: Message):
    await message.reply(
        "欢迎使用 yakusoku (約束, 约定)\n\n"
        "yakusoku 是一个多功能机器人, 有什么想法的都可以提出 Issue, 也欢迎大家来提交 PR.\n\n"
        f"Git 仓库: [GitLab]({constants.GITLAB_REPOSITORY_URL}) (仅有公开查看权限)  "
        f"[GitHub]({constants.GITHUB_REPOSITORY_URL})",
        parse_mode=ParseMode.MARKDOWN,
    )
