"""Application bootstrap wiring."""
from __future__ import annotations

import asyncio
import logging
import threading
from pathlib import Path
from typing import Any

from .config import AppConfig, load_config, load_media_profile, load_scenario
from .logging.config import setup_logging
from .peers.manager import PeerManager
from .metrics.collector import MetricsCollector
from .signaling.app import create_signaling_app

logger = logging.getLogger(__name__)


class BootstrapContext:
    def __init__(self, config: AppConfig, app, manager: PeerManager, metrics: MetricsCollector, loop: asyncio.AbstractEventLoop):
        self.config = config
        self.app = app
        self.manager = manager
        self.metrics = metrics
        self.loop = loop
        self._loop_thread: threading.Thread | None = None

    def start_loop(self) -> None:
        if self._loop_thread:
            return
        self._loop_thread = threading.Thread(target=self.loop.run_forever, name="asyncio-runtime", daemon=True)
        self._loop_thread.start()

    def shutdown(self) -> None:
        if self.metrics:
            self.loop.call_soon_threadsafe(asyncio.create_task, self.metrics.stop())
        if self.manager:
            self.loop.call_soon_threadsafe(asyncio.create_task, self.manager.shutdown())
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self._loop_thread:
            self._loop_thread.join(timeout=2)


def bootstrap(app_config_path: Path) -> BootstrapContext:
    config = load_config(app_config_path)
    setup_logging(config.logging_path)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    manager = PeerManager()
    metrics = MetricsCollector(manager.registry, loop=loop, exporter="log")

    # Preload scenario and media profiles for headless mode (no direct use here, but validated early)
    try:
        load_scenario(config.headless_scenario_file)
    except Exception as exc:  # pragma: no cover - optional
        logger.warning("scenario load failed", exc_info=exc)
    try:
        load_media_profile(Path("configs/media/default-video.yaml"), Path("configs/media/default-audio.yaml"))
    except Exception as exc:  # pragma: no cover - optional
        logger.warning("media profile load failed", exc_info=exc)

    app = create_signaling_app(session_ttl=config.signaling.session_ttl_seconds)
    # control plane routes
    from .control.api import create_control_blueprint
    from .control.service import ControlService
    from .control.ui_routes import create_ui_blueprint

    service = ControlService(manager)
    app.register_blueprint(create_control_blueprint(service))
    app.register_blueprint(create_ui_blueprint())

    ctx = BootstrapContext(config=config, app=app, manager=manager, metrics=metrics, loop=loop)
    return ctx
