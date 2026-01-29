from __future__ import annotations

from typing import Optional

import requests

from app.utils.validators import allowed_extension


def resolve_external(resolver_url: str, kind: str, url: str, allowed_ext: set[str], timeout: int) -> Optional[str]:
    if not resolver_url:
        return None
    try:
        resp = requests.post(
            resolver_url,
            json={"kind": kind, "url": url},
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json() if resp.content else {}
        resolved = data.get("url")
        if resolved and allowed_extension(resolved, allowed_ext):
            return resolved
    except Exception:
        return None
    return None

