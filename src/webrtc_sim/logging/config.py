"""Logging configuration utilities."""
from __future__ import annotations

import logging
import logging.config
from pathlib import Path
import yaml

try:
    import pythonjsonlogger  # type: ignore  # noqa: F401
    _json_available = True
except ImportError:  # pragma: no cover
    _json_available = False


def setup_logging(logging_config_path: Path | None = None) -> None:
    if logging_config_path and logging_config_path.exists():
        with logging_config_path.open("r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh) or {}
        if config:
            logging.config.dictConfig(_translate_config(config))
            return
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


def _translate_config(config: dict) -> dict:
    """Translate custom yaml structure into logging.dictConfig format."""
    level = config.get("logging", {}).get("level", "INFO")
    fmt = config.get("logging", {}).get("format", "json")
    sinks = config.get("sinks", [])

    handlers = {}
    handler_names = []
    for idx, sink in enumerate(sinks or [{"type": "stdout"}]):
        name = f"h{idx}"
        handler_names.append(name)
        if sink.get("type") == "stdout":
            handlers[name] = {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "json" if (fmt == "json" and _json_available) else "plain",
                "level": level,
            }

    formatters = {
        "plain": {"format": "%(asctime)s %(levelname)s %(name)s %(message)s"},
    }
    if _json_available:
        formatters["json"] = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(peer_id)s %(session_id)s %(scenario_id)s",
        }

    # Fallback handler if no sinks are configured
    if not handlers:
        handlers["console"] = {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "formatter": "plain",
            "level": level,
        }
        handler_names.append("console")

    return {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": formatters,
        "handlers": handlers,
        "root": {"level": level, "handlers": handler_names},
    }
