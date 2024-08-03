import html

from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from yakusoku.context import module_manager
from yakusoku.utils import exception

router = module_manager.create_router()


@router.message(Command("int"))
async def int_cmd(message: Message, command: CommandObject):
    inp = command.args

    if not inp:
        return await message.reply("没给我数字不知道你想要了解什么捏w")

    inp = inp.strip()

    if (number := exception.try_or_default(lambda: int(inp, 0), None)) is None:
        return await message.reply("这是个整数吗, 别欺负我读书少x")

    lines: list[str] = []
    lines.append(f"输入 (Input): <code>{inp}</code>")

    lines.extend(
        [
            f"十进制 (Decimal): <code>{number:d}</code>",
            f"二进制 (Binary): <code>{number:b}</code>",
            f"八进制 (Octal): <code>{number:o}</code>",
            f"十六进制 (Hex): <code>{number:x}</code>",
        ]
    )

    if number > 0 and (byte_length := (number.bit_length() + 7) // 8) <= 16:
        be_bytes = number.to_bytes(byte_length, "big")
        le_bytes = number.to_bytes(byte_length, "little")
        be_str = exception.try_or_default(lambda: be_bytes.decode())
        le_str = exception.try_or_default(lambda: le_bytes.decode())
        lines.extend(
            [
                f"字符串 (大端序) (BE String): <code>{html.escape(repr(be_str or be_bytes))}</code>",
                f"字符串 (小端序) (LE String): <code>{html.escape(repr(le_str or le_bytes))}</code>",
            ]
        )

    await message.reply("\n".join(lines))
