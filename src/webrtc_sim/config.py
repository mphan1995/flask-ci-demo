"""Configuration loading and validation utilities."""
from __future__ import annotations

import os
import typing as t
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class MediaProfileConfig:
    video_profile: str
    audio_profile: str


@dataclass(frozen=True)
class ScenarioConfig:
    id: str
    mode: str
    count: int
    startup_strategy: str
    peers_per_second: int | None = None
    churn_enabled: bool = False
    join_leave_interval_seconds: int | None = None
    video_profile: str = "default-video"
    audio_profile: str = "default-audio"


@dataclass(frozen=True)
class SignalingConfig:
    transport: str = "websocket"
    http_enabled: bool = True
    ws_enabled: bool = True
    session_ttl_seconds: int = 180


@dataclass(frozen=True)
class ControlPlaneConfig:
    api_enabled: bool = True
    web_ui_enabled: bool = True


@dataclass(frozen=True)
class PeerDefaults:
    default_count: int = 1
    max_count: int = 1000
    join_strategy: str = "staggered"


@dataclass(frozen=True)
class RuntimeConfig:
    asyncio_policy: str = "default"
    shutdown_grace_seconds: int = 15


@dataclass(frozen=True)
class AppConfig:
    name: str
    mode: str
    host: str
    port: int
    runtime: RuntimeConfig
    control_plane: ControlPlaneConfig
    signaling: SignalingConfig
    peers: PeerDefaults
    headless_scenario_file: Path | None
    interactive_ui_path: str
    logging_path: Path | None = None

    @property
    def is_headless(self) -> bool:
        return self.mode.lower() == "headless"


class ConfigError(RuntimeError):
    """Raised when configuration is invalid."""


def _env_override(key: str, default: t.Any, env: t.Mapping[str, str]) -> t.Any:
    if key not in env:
        return default
    value = env[key]
    # Basic type coercion
    if isinstance(default, bool):
        return value.lower() in {"1", "true", "yes", "on"}
    if isinstance(default, int):
        try:
            return int(value)
        except ValueError:
            return default
    return value


def load_yaml(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ConfigError(f"Config file malformed: {path}")
    return data


def load_config(app_path: Path, env: t.Mapping[str, str] | None = None) -> AppConfig:
    env = env or os.environ
    data = load_yaml(app_path)
    app = data.get("app", {})
    runtime = data.get("runtime", {})
    control = data.get("control_plane", {})
    signaling = data.get("signaling", {})
    peers = data.get("peers", {})
    headless = data.get("headless", {})
    interactive = data.get("interactive", {})

    name = app.get("name", "webrtc-peer-simulator")
    mode = _env_override("WRTC_SIM_MODE", app.get("mode", "headless"), env)
    host = _env_override("WRTC_SIM_HOST", app.get("host", "0.0.0.0"), env)
    port = _env_override("WRTC_SIM_PORT", app.get("port", 8080), env)

    runtime_cfg = RuntimeConfig(
        asyncio_policy=runtime.get("asyncio_policy", "default"),
        shutdown_grace_seconds=int(runtime.get("shutdown_grace_seconds", 15)),
    )

    control_cfg = ControlPlaneConfig(
        api_enabled=bool(_env_override("WRTC_CONTROL_API", control.get("api_enabled", True), env)),
        web_ui_enabled=bool(_env_override("WRTC_CONTROL_UI", control.get("web_ui_enabled", True), env)),
    )

    signaling_cfg = SignalingConfig(
        transport=_env_override("WRTC_SIGNALING_TRANSPORT", signaling.get("transport", "websocket"), env),
        http_enabled=bool(_env_override("WRTC_SIGNALING_HTTP_ENABLED", signaling.get("http_enabled", True), env)),
        ws_enabled=bool(_env_override("WRTC_SIGNALING_WS_ENABLED", signaling.get("ws_enabled", True), env)),
        session_ttl_seconds=int(signaling.get("session_ttl_seconds", 180)),
    )

    peer_defaults = PeerDefaults(
        default_count=int(_env_override("WRTC_PEER_DEFAULT_COUNT", peers.get("default_count", 1), env)),
        max_count=int(peers.get("max_count", 1000)),
        join_strategy=peers.get("join_strategy", "staggered"),
    )

    headless_file = headless.get("scenario_file")
    if headless_file:
        headless_path = Path(headless_file)
    else:
        headless_path = Path(_env_override("WRTC_SCENARIO_FILE", "configs/scenarios/single-peer.yaml", env))

    interactive_ui_path = interactive.get("browser_ui_path", "/ui")

    return AppConfig(
        name=name,
        mode=mode,
        host=host,
        port=int(port),
        runtime=runtime_cfg,
        control_plane=control_cfg,
        signaling=signaling_cfg,
        peers=peer_defaults,
        headless_scenario_file=headless_path,
        interactive_ui_path=interactive_ui_path,
        logging_path=Path("configs/logging.yaml"),
    )


def load_scenario(path: Path) -> ScenarioConfig:
    data = load_yaml(path)
    scenario_meta = data.get("scenario", {})
    peer_cfg = data.get("peers", {})
    churn = peer_cfg.get("churn", {})
    media_profile = data.get("media_profile", {})
    lifecycle = data.get("lifecycle", {})

    return ScenarioConfig(
        id=scenario_meta.get("id", path.stem),
        mode=scenario_meta.get("mode", "headless"),
        count=int(peer_cfg.get("count", 1)),
        startup_strategy=peer_cfg.get("startup", {}).get("strategy", "immediate"),
        peers_per_second=peer_cfg.get("startup", {}).get("peers_per_second"),
        churn_enabled=bool(churn.get("enabled", False)),
        join_leave_interval_seconds=churn.get("join_leave_interval_seconds"),
        video_profile=media_profile.get("video_profile", lifecycle.get("video_profile", "default-video")),
        audio_profile=media_profile.get("audio_profile", lifecycle.get("audio_profile", "default-audio")),
    )


def load_media_profile(video_path: Path, audio_path: Path) -> dict:
    return {
        "video": load_yaml(video_path).get("video", {}),
        "audio": load_yaml(audio_path).get("audio", {}),
    }
