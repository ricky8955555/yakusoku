import asyncio
import contextlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable
from uuid import UUID, uuid1

from aiogram import Router
from aiogram.filters.callback_data import CallbackData, CallbackQueryFilter
from aiogram.types import CallbackQuery

UserCallback = Callable[[CallbackQuery], Awaitable[Any]]
DisposedCallback = Callable[[], Awaitable[Any]]


@dataclass
class CallbackQueryTask:
    uuid: UUID
    disposable: bool
    user_callback: UserCallback
    callback_data: str
    expiry: datetime | None
    disposed: DisposedCallback | None = None


class _CallbackQueryTaskData(CallbackData, prefix="task"):
    uuid: UUID


class CallbackQueryTaskFilter(CallbackQueryFilter):
    pass


class CallbackQueryTaskManager:
    _tasks: dict[UUID, CallbackQueryTask]
    _cancellation_tasks: dict[UUID, CallbackQueryTask]
    _error_answer: str | None
    _expire_tasks: list[asyncio.Task[None]]
    _callback_data: type[_CallbackQueryTaskData]

    def __init__(self, router: Router, query_prefix: str, error_answer: str | None = None) -> None:
        self._tasks = {}
        self._error_answer = error_answer
        self._expire_tasks = []
        self._cancellation_tasks = {}
        self._callback_data = type(
            f"_CallbackQueryTaskData_{query_prefix}",
            (_CallbackQueryTaskData,),
            {},
            prefix=query_prefix,
        )
        self._callback_data.__prefix__ = query_prefix
        router.callback_query.register(
            self._handle_callback_query_task, CallbackQueryFilter(callback_data=self._callback_data)
        )

    def create_task(
        self,
        callback: UserCallback,
        disposable: bool = True,
        expired_after: timedelta | None = None,
        disposed: DisposedCallback | None = None,
    ) -> CallbackQueryTask:
        uuid = uuid1()

        if expired_after:

            async def expirable_disposed():
                expire_task.cancel()
                self._expire_tasks.remove(expire_task)
                if disposed:
                    await disposed()

            async def expire():
                await asyncio.sleep(expired_after.total_seconds())
                self._expire_tasks.remove(expire_task)
                del self._tasks[uuid]
                if disposed:
                    await disposed()

            task = self._tasks[uuid] = CallbackQueryTask(
                uuid,
                disposable,
                callback,
                self._callback_data(uuid=uuid).pack(),
                datetime.now() + expired_after,
                expirable_disposed,
            )
            expire_task = asyncio.create_task(expire())
            self._expire_tasks.append(expire_task)
            return task

        task = self._tasks[uuid] = CallbackQueryTask(
            uuid, disposable, callback, self._callback_data(uuid=uuid).pack(), None
        )
        return task

    async def cancel_task(self, task: CallbackQueryTask) -> None:
        with contextlib.suppress(KeyError):
            del self._tasks[task.uuid]
        if task.disposed:
            with contextlib.suppress(Exception):
                await task.disposed()
        if cancellation_task := self._cancellation_tasks.get(task.uuid):
            await self.cancel_task(cancellation_task)

    def create_cancellation_task(
        self,
        task: CallbackQueryTask,
        post_callback: UserCallback | None = None,
        cancelled_answer: str | None = None,
    ) -> CallbackQueryTask:
        assert task.uuid not in self._cancellation_tasks

        async def cancel(query: CallbackQuery):
            await self.cancel_task(task)
            if post_callback:
                await post_callback(query)
            await query.answer(cancelled_answer)

        expired_after = task.expiry - datetime.now() if task.expiry else None
        cancellation_task = self.create_task(
            cancel,
            expired_after=expired_after,
        )
        self._cancellation_tasks[task.uuid] = cancellation_task
        return cancellation_task

    async def _handle_callback_query_task(
        self, query: CallbackQuery, callback_data: _CallbackQueryTaskData
    ):
        if not (task := self._tasks.get(callback_data.uuid)):
            return await query.answer(self._error_answer)
        result = await task.user_callback(query)
        if task.disposable and result != False:
            await self.cancel_task(task)
