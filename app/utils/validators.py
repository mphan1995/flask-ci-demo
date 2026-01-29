from __future__ import annotations

from urllib.parse import urlparse
import ipaddress

YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}
NHACCUATUI_HOSTS = {
    "nhaccuatui.com",
    "www.nhaccuatui.com",
}
ZINGMP3_HOSTS = {
    "zingmp3.vn",
    "www.zingmp3.vn",
    "mp3.zing.vn",
}


def is_safe_url(url: str, allow_private: bool = False) -> bool:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        return False
    host = parsed.hostname
    if not host:
        return False

    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            return allow_private
    except ValueError:
        # hostname, basic allowlist logic could be added here
        pass

    return True


def allowed_extension(url: str, allowed_ext: set[str]) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()
    if not path:
        return False
    return any(path.endswith(ext) for ext in allowed_ext)


def normalize_url(raw_url: str) -> str | None:
    raw = (raw_url or "").strip()
    if not raw:
        return None
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    if raw.startswith("//"):
        return f"https:{raw}"
    if raw.startswith("www."):
        return f"https://{raw}"
    if "." in raw and " " not in raw:
        return f"https://{raw}"
    return raw


def classify_url(raw_url: str, allowed_ext: set[str]) -> dict:
    normalized = normalize_url(raw_url)
    if not normalized:
        return {"valid": False, "reason": "empty"}
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    if host in YOUTUBE_HOSTS:
        return {"valid": True, "kind": "youtube", "url": normalized}
    if host in NHACCUATUI_HOSTS:
        return {"valid": True, "kind": "nhaccuatui", "url": normalized}
    if host in ZINGMP3_HOSTS:
        return {"valid": True, "kind": "zingmp3", "url": normalized}
    if allowed_extension(normalized, allowed_ext):
        return {"valid": True, "kind": "audio", "url": normalized}
    return {"valid": False, "reason": "unsupported"}
