import re

from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from yakusoku.context import module_manager

from . import mastercard

router = module_manager.create_router()

CURCONV_PATTERN = re.compile(
    r"^(?:(?P<amt>\d+(?:\.\d+)?)\s?)?(?P<src>[a-zA-Z]+)(?:\s(?P<dest>[a-zA-Z]+))?$"
)


@router.message(Command("curconv"))
async def curconv(message: Message, command: CommandObject):
    if not command.args or not (matches := CURCONV_PATTERN.match(command.args)):
        return await message.reply(
            "戳啦, 正确用法为 `/curconv [货币数量 (置空只输出汇率)]<源货币> [目标货币 (默认为 CNY)]`\n"
            "示例: `/curconv 114EUR JPY`",
            parse_mode=ParseMode.MARKDOWN,
        )

    amount = matches.group("amt")
    trans_amt = float(amount) if amount else 1

    src = matches.group("src")
    dest = matches.group("dest") or "CNY"

    try:
        data = await mastercard.conversion_rate(
            trans_curr=src, crdhld_bill_curr=dest, trans_amt=trans_amt
        )
    except mastercard.ApiError as ex:
        return await message.reply(f"API 请求错误惹w\n错误码: {ex.code}\n错误消息: {ex.message}")
    except Exception as ex:
        return await message.reply(f"呜呜呜, 咱也不知道发生了什么事w\n{ex}")

    lines: list[str] = []

    if amount:
        lines.append(
            f"<code>{data.trans_amt}</code> {data.trans_curr} = <code>{data.crdhld_bill_amt}</code> {data.crdhld_bill_curr}\n"
        )

    lines.append(
        f"{data.trans_curr} -> {data.crdhld_bill_curr} 汇率: <code>{data.conversion_rate}</code>"
    )
    lines.append(f"汇率更新时间: {data.fx_date}")

    await message.reply("\n".join(lines))
