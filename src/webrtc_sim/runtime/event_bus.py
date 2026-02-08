"""Simple asyncio event bus for decoupled communication."""
from __future__ import annotations

import asyncio
import typing as t
from collections import defaultdict


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def publish(self, topic: str, payload: t.Any) -> None:
        async with self._lock:
            queues = list(self._subscribers.get(topic, []))
        for queue in queues:
            await queue.put(payload)

    async def subscribe(self, topic: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            self._subscribers[topic].append(queue)
        return queue

    async def unsubscribe(self, topic: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            if topic in self._subscribers and queue in self._subscribers[topic]:
                self._subscribers[topic].remove(queue)


def create_event_bus() -> EventBus:
    return EventBus()
