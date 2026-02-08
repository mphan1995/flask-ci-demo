"""CLI entrypoint."""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from dataclasses import replace
from pathlib import Path

from .bootstrap import bootstrap

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="WebRTC Peer Simulator")
    parser.add_argument("--config", default="configs/app.yaml", help="Path to app config yaml")
    parser.add_argument("--mode", choices=["headless", "interactive"], help="Override mode")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    ctx = bootstrap(Path(args.config))
    mode = args.mode or ctx.config.mode
    # create a copy of config with mode override (AppConfig is frozen)
    ctx.config = replace(ctx.config, mode=mode)  # type: ignore[attr-defined]

    ctx.start_loop()
    ctx.metrics.start()

    def handle_signal(*_: int):
        logger.info("shutdown requested")
        ctx.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    ctx.app.run(host=ctx.config.host, port=ctx.config.port, threaded=True)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
