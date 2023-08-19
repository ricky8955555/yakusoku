import contextlib
import inspect
from dataclasses import dataclass
from datetime import datetime, timedelta
from threading import Timer
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


def _custom_filter_to_filter(filter: CustomFilter) -> Filter:
    async def async_filter_wrapper(query: CallbackQuery) -> bool:
        return filter(query)  # type: ignore

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

    @property
    def callback_data(self) -> str:
        return f"{self.query_prefix}{self.uuid}"


class CallbackQueryTaskManager:
    _tasks: dict[UUID, CallbackQueryTask]
    _query_prefix: str
    _error_answer: str | None
    _timers: list[Timer]

    def __init__(
        self, dispatcher: Dispatcher, query_prefix: str = "task/", error_answer: str | None = None
    ) -> None:
        self._tasks = {}
        self._query_prefix = query_prefix
        self._error_answer = error_answer
        self._timers = []
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
    ) -> CallbackQueryTask:
        filters = [_unify_filter(filter, fallback_answer) for filter in custom_filters]
        uuid = uuid1()

        if expired_after:

            def remove_task():
                del self._tasks[uuid]
                self._timers.remove(timer)

            async def expirable_callback(query: CallbackQuery):
                await callback(query)
                self._timers.remove(timer)

            timer = Timer(expired_after.total_seconds(), remove_task)
            self._timers.append(timer)
            task = self._tasks[uuid] = CallbackQueryTask(
                uuid,
                description,
                disposable,
                expirable_callback,
                filters,
                self._query_prefix,
                datetime.now() + expired_after,
            )
            return task

        task = self._tasks[uuid] = CallbackQueryTask(
            uuid, description, disposable, callback, filters, self._query_prefix, None
        )
        return task

    def create_cancellation_task(
        self,
        task: CallbackQueryTask,
        custom_filters: list[CustomFilter | AnsweredCustomFilter] | None = None,
        post_callback: UserCallback | None = None,
        fallback_answer: str = "",
        cancelled_answer: str | None = None,
    ) -> CallbackQueryTask:
        async def cancel_task(query: CallbackQuery):
            with contextlib.suppress(KeyError):
                del self._tasks[task.uuid]
            if post_callback:
                await post_callback(query)
            await query.answer(cancelled_answer)

        expired_after = task.expired_on - datetime.now() if task.expired_on else None
        return self.create_task(
            cancel_task,
            task.filters if custom_filters is None else custom_filters,  # type: ignore
            fallback_answer=fallback_answer,
            expired_after=expired_after,
        )

    async def _handle_callback_query_task(self, query: CallbackQuery):  # type: ignore
        uuid = query.data.removeprefix(self._query_prefix)
        if not (task := self._tasks.get(UUID(uuid))):
            return await query.answer(self._error_answer)
        for filter, answer in task.filters:
            if not await filter(query):
                return await query.answer(answer)
        await task.user_callback(query)
        if task.disposable:
            del self._tasks[task.uuid]
