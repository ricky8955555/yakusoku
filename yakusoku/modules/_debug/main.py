import json
import re
from datetime import timedelta

from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from yakusoku.modules import command_handler, dispatcher
from yakusoku.shared.callback import CallbackQueryTaskManager

dp = dispatcher()

tasks = CallbackQueryTaskManager(dp, "debug_task/", "QwQ")

PATTERN = re.compile(r"《(.+)》")


def score(name: str) -> float:
    result = abs(hash(name))
    while result > 100:
        result >>= 1
    return result / 10


@dp.message_handler()
async def message_received(message: Message):
    matches = PATTERN.match(message.text)
    if not matches:
        return
    scored = score(matches.group(1))
    await message.reply(f"豆瓣评分: {scored}")


@command_handler(["raw"], "获取消息元数据")
async def raw(message: Message):
    data = json.dumps(message.to_python(), indent=2, sort_keys=True, ensure_ascii=False)
    await message.reply(f'<pre language="html">{data}</pre>')


@command_handler(["create_task"], "创建任务 (测试)")
async def create_task(message: Message):
    async def callback(query: CallbackQuery):
        await query.answer("好哦!")

    expired_after = timedelta(seconds=float(args)) if (args := message.get_args()) else None
    task = tasks.create_task(callback, expired_after=expired_after)
    markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="按!", callback_data=task.callback_data)]  # type: ignore
        ]
    )
    await message.reply("!", reply_markup=markup)
