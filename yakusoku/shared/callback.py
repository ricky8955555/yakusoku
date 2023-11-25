import asyncio
import contextlib
import inspect
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable
from uuid import UUID, uuid1

from aiogram import Dispatcher
from aiogram.dispatcher.filters import AbstractFilter
from aiogram.types import CallbackQuery

from yakusoku.filters import CallbackQueryFilter

Filter = Callable[[CallbackQuery], Awaitable[bool]]
CustomFilter = AbstractFilter | Callable[[CallbackQuery], bool] | Filter
AnsweredFilter = tuple[Filter, str]
AnsweredCustomFilter = tuple[CustomFilter, str]
UserCallback = Callable[[CallbackQuery], Awaitable[Any]]
DisposedCallback = Callable[[], Awaitable[Any]]


def _custom_filter_to_filter(filter: CustomFilter) -> Filter:
    async def async_filter_wrapper(query: CallbackQuery) -> bool:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: filter(query))  # type: ignore

    if isinstance(filter, AbstractFilter):
        return filter.check
    if not inspect.iscoroutinefunction(filter):
        return async_filter_wrapper
    return filter


def _unify_filter(
    filter: CustomFilter | AnsweredCustomFilter, fallback_answer: str
) -> AnsweredFilter:
    if isinstance(filter, tuple):
        filter, answer = filter
    else:
        answer = fallback_answer
    return _custom_filter_to_filter(filter), answer


@dataclass(frozen=True)
class CallbackQueryTask:
    uuid: UUID
    description: str | None
    disposable: bool
    user_callback: UserCallback
    filters: list[AnsweredFilter]
    query_prefix: str
    expired_on: datetime | None
    disposed: DisposedCallback | None = None

    @property
    def callback_data(self) -> str:
        return f"{self.query_prefix}{self.uuid}"


class CallbackQueryTaskManager:
    _tasks: dict[UUID, CallbackQueryTask]
    _cancellation_tasks: dict[UUID, CallbackQueryTask]
    _query_prefix: str
    _error_answer: str | None
    _expire_tasks: list[asyncio.Task[None]]

    def __init__(
        self, dispatcher: Dispatcher, query_prefix: str = "task/", error_answer: str | None = None
    ) -> None:
        self._tasks = {}
        self._query_prefix = query_prefix
        self._error_answer = error_answer
        self._expire_tasks = []
        self._cancellation_tasks = {}
        dispatcher.register_callback_query_handler(
            self._handle_callback_query_task, CallbackQueryFilter(query_prefix)
        )

    def create_task(
        self,
        callback: UserCallback,
        custom_filters: list[CustomFilter | AnsweredCustomFilter] = [],
        description: str | None = None,
        fallback_answer: str = "",
        disposable: bool = True,
        expired_after: timedelta | None = None,
        disposed: DisposedCallback | None = None,
    ) -> CallbackQueryTask:
        filters = [_unify_filter(filter, fallback_answer) for filter in custom_filters]
        uuid = uuid1()

        if expired_after:

            async def expirable_disposed():
                if disposed:
                    await disposed()
                expire_task.cancel()
                self._expire_tasks.remove(expire_task)

            async def expire():
                await asyncio.sleep(expired_after.total_seconds())
                if disposed:
                    await disposed()
                self._expire_tasks.remove(expire_task)
                del self._tasks[uuid]

            task = self._tasks[uuid] = CallbackQueryTask(
                uuid,
                description,
                disposable,
                callback,
                filters,
                self._query_prefix,
                datetime.now() + expired_after,
                expirable_disposed,
            )
            expire_task = asyncio.create_task(expire())
            self._expire_tasks.append(expire_task)
            return task

        task = self._tasks[uuid] = CallbackQueryTask(
            uuid, description, disposable, callback, filters, self._query_prefix, None
        )
        return task

    async def cancel_task(self, task: CallbackQueryTask):
        with contextlib.suppress(KeyError):
            del self._tasks[task.uuid]
        if task.disposed:
            await task.disposed()
        if cancellation_task := self._cancellation_tasks.get(task.uuid):
            await self.cancel_task(cancellation_task)

    def create_cancellation_task(
        self,
        task: CallbackQueryTask,
        custom_filters: list[CustomFilter | AnsweredCustomFilter] | None = None,
        post_callback: UserCallback | None = None,
        fallback_answer: str = "",
        cancelled_answer: str | None = None,
    ) -> CallbackQueryTask:
        assert task.uuid not in self._cancellation_tasks

        async def cancel(query: CallbackQuery):
            await self.cancel_task(task)
            if post_callback:
                await post_callback(query)
            await query.answer(cancelled_answer)

        expired_after = task.expired_on - datetime.now() if task.expired_on else None
        cancellation_task = self.create_task(
            cancel,
            task.filters if custom_filters is None else custom_filters,  # type: ignore
            fallback_answer=fallback_answer,
            expired_after=expired_after,
        )
        self._cancellation_tasks[task.uuid] = cancellation_task
        return cancellation_task

    async def _handle_callback_query_task(self, query: CallbackQuery):  # type: ignore
        uuid = query.data.removeprefix(self._query_prefix)
        if not (task := self._tasks.get(UUID(uuid))):
            return await query.answer(self._error_answer)
        for filter, answer in task.filters:
            if not await filter(query):
                return await query.answer(answer)
        await task.user_callback(query)
        if task.disposable:
            await self.cancel_task(task)
