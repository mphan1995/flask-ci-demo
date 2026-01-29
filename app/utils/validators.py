from __future__ import annotations

from urllib.parse import urlparse
import ipaddress


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

