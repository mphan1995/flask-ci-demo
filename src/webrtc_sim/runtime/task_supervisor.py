"""Async task supervision utilities."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

logger = logging.getLogger(__name__)


class TaskSupervisor:
    def __init__(self) -> None:
        self._tasks: set[asyncio.Task] = set()

    def create(self, name: str, coro: Awaitable) -> asyncio.Task:
        task = asyncio.create_task(coro, name=name)
        task.add_done_callback(self._log_result)
        self._tasks.add(task)
        return task

    async def shutdown(self, timeout: float = 10.0) -> None:
        if not self._tasks:
            return
        for task in self._tasks:
            task.cancel()
        await asyncio.wait(self._tasks, timeout=timeout)

    def _log_result(self, task: asyncio.Task) -> None:
        self._tasks.discard(task)
        try:
            exc = task.exception()
        except asyncio.CancelledError:
            return
        if exc:
            logger.error("task failed", exc_info=exc)
