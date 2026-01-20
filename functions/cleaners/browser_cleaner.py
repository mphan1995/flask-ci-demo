import os

from ..security import (
    DEFAULT_EXCLUSIONS,
    get_dir_size,
    is_path_allowed,
    is_windows,
    run_powershell,
    safe_delete_contents,
    safe_delete_file,
)

BROWSER_PROCESS_NAMES = ["chrome", "msedge", "firefox"]


def _get_running_browsers():
    if not is_windows():
        return []
    cmd = (
        "Get-Process -Name chrome,msedge,firefox -ErrorAction SilentlyContinue "
        "| Select-Object -ExpandProperty Name"
    )
    result = run_powershell(cmd)
    if not result.get("ok"):
        return []
    names = []
    for line in result.get("stdout", "").splitlines():
        name = line.strip().lower()
        if name:
            names.append(name)
    return sorted(set(names))


def _collect_targets():
    targets = []
    local_app_data = os.getenv("LOCALAPPDATA", "")
    app_data = os.getenv("APPDATA", "")

    chrome_base = os.path.join(local_app_data, "Google", "Chrome", "User Data", "Default")
    edge_base = os.path.join(local_app_data, "Microsoft", "Edge", "User Data", "Default")

    chrome_paths = [
        os.path.join(chrome_base, "Cache"),
        os.path.join(chrome_base, "Code Cache"),
        os.path.join(chrome_base, "GPUCache"),
        os.path.join(chrome_base, "Cookies"),
    ]
    edge_paths = [
        os.path.join(edge_base, "Cache"),
        os.path.join(edge_base, "Code Cache"),
        os.path.join(edge_base, "GPUCache"),
        os.path.join(edge_base, "Cookies"),
    ]

    for path in chrome_paths:
        if os.path.exists(path):
            targets.append({"browser": "Chrome", "path": path})
    for path in edge_paths:
        if os.path.exists(path):
            targets.append({"browser": "Edge", "path": path})

    firefox_profiles = os.path.join(app_data, "Mozilla", "Firefox", "Profiles")
    if os.path.isdir(firefox_profiles):
        for entry in os.listdir(firefox_profiles):
            profile_path = os.path.join(firefox_profiles, entry)
            if not os.path.isdir(profile_path):
                continue
            for path in [
                os.path.join(profile_path, "cache2"),
                os.path.join(profile_path, "cookies.sqlite"),
            ]:
                if os.path.exists(path):
                    targets.append({"browser": "Firefox", "path": path})

    return targets


def _allowed_roots(targets):
    roots = set()
    for item in targets:
        path = item["path"]
        if "Chrome" in item["browser"]:
            roots.add(os.path.dirname(os.path.dirname(path)))
        elif "Edge" in item["browser"]:
            roots.add(os.path.dirname(os.path.dirname(path)))
        elif "Firefox" in item["browser"]:
            roots.add(os.path.dirname(path))
    return list(roots)


def scan_browser_cache():
    if not is_windows():
        return {"ok": False, "error": "windows_only"}

    running = _get_running_browsers()
    if running:
        return {
            "ok": False,
            "error": "browser_running",
            "running": running,
            "notes": "Close browsers before scanning cache.",
        }

    targets = _collect_targets()
    allowed_roots = _allowed_roots(targets)

    total = 0
    items = []
    errors = []

    for target in targets:
        path = target["path"]
        if not is_path_allowed(path, allowed_roots):
            continue
        if os.path.isdir(path):
            size_info = get_dir_size(
                path,
                exclusions=DEFAULT_EXCLUSIONS,
                max_files=200000,
                max_depth=8,
            )
            size = size_info["bytes"]
            errors.extend(size_info["errors"])
        else:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
        total += size
        items.append({"browser": target["browser"], "path": path, "bytes": size})

    return {
        "ok": True,
        "bytes": total,
        "items": items,
        "errors": errors,
    }


def run_browser_cache(dry_run=False):
    if not is_windows():
        return {"ok": False, "error": "windows_only"}

    running = _get_running_browsers()
    if running:
        return {
            "ok": False,
            "error": "browser_running",
            "running": running,
            "notes": "Close browsers before cleaning cache.",
        }

    targets = _collect_targets()
    allowed_roots = _allowed_roots(targets)

    total = 0
    deleted = 0
    errors = []

    for target in targets:
        path = target["path"]
        if not is_path_allowed(path, allowed_roots):
            continue
        if os.path.isdir(path):
            result = safe_delete_contents(
                path,
                allowed_roots=allowed_roots,
                dry_run=dry_run,
                exclusions=DEFAULT_EXCLUSIONS,
                max_files=200000,
            )
            total += result.get("bytes", 0)
            deleted += result.get("files_deleted", 0)
            errors.extend(result.get("errors", []))
        else:
            try:
                size = os.path.getsize(path)
            except OSError:
                size = 0
            total += size
            result = safe_delete_file(path, allowed_roots=allowed_roots, dry_run=dry_run)
            if not result.get("ok"):
                errors.append(result.get("error", "delete_failed"))
            else:
                deleted += 1

    return {
        "ok": len(errors) == 0,
        "bytes": total,
        "files_deleted": deleted,
        "errors": errors,
        "dry_run": dry_run,
    }
