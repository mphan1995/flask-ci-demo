"""Metrics exporters."""
from __future__ import annotations

import logging
from typing import Iterable

from .models import PeerMetrics

logger = logging.getLogger(__name__)


class MetricsExporter:
    def export(self, samples: Iterable[PeerMetrics]) -> None:  # pragma: no cover - interface
        raise NotImplementedError


class LogExporter(MetricsExporter):
    def export(self, samples: Iterable[PeerMetrics]) -> None:
        for sample in samples:
            logger.info("metrics", extra=sample.as_dict())


EXPORTER_REGISTRY = {
    "log": LogExporter,
}


def get_exporter(name: str) -> MetricsExporter:
    cls = EXPORTER_REGISTRY.get(name, LogExporter)
    return cls()
