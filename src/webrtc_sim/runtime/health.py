"""Health and readiness checks."""
from __future__ import annotations

import time
from dataclasses import dataclass


@dataclass
class HealthStatus:
    healthy: bool
    ready: bool
    started_at: float

    def as_dict(self) -> dict:
        return {"healthy": self.healthy, "ready": self.ready, "uptime_seconds": time.time() - self.started_at}


def create_health_status() -> HealthStatus:
    return HealthStatus(healthy=True, ready=False, started_at=time.time())
