"""Periodic metric collection."""
from __future__ import annotations

import asyncio
import logging
from typing import Iterable

from .exporters import get_exporter, MetricsExporter
from .stats_adapter import from_aiortc
from .models import PeerMetrics

logger = logging.getLogger(__name__)


class MetricsCollector:
    def __init__(self, registry, loop: asyncio.AbstractEventLoop, interval_seconds: float = 5.0, exporter: str = "log") -> None:
        self.registry = registry
        self.loop = loop
        self.interval = interval_seconds
        self.exporter: MetricsExporter = get_exporter(exporter)
        self._task: asyncio.Task | None = None
        self._stopped = asyncio.Event()

    def start(self) -> None:
        if self._task:
            return
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self._spawn)
        else:
            self.loop.create_task(self._run(), name="metrics-collector")

    def _spawn(self) -> None:
        if not self._task:
            self._task = self.loop.create_task(self._run(), name="metrics-collector")

    async def stop(self) -> None:
        if self._task:
            self._stopped.set()
            await self._task

    async def _run(self) -> None:
        while not self._stopped.is_set():
            await asyncio.sleep(self.interval)
            try:
                samples = await self._collect_once()
                if samples:
                    self.exporter.export(samples)
            except Exception as exc:  # pragma: no cover - safety
                logger.error("metrics collection failed", exc_info=exc)

    async def _collect_once(self) -> Iterable[PeerMetrics]:
        samples: list[PeerMetrics] = []
        for peer in self.registry.all():
            stats = await peer.get_stats()
            samples.append(from_aiortc(peer.peer_id, stats))
        return samples
