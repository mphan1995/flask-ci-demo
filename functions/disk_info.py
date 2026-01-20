import ctypes
import os
import shutil

from .security import DEFAULT_EXCLUSIONS, get_dir_size, is_windows


def format_bytes(num):
    step = 1024.0
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(num)
    for unit in units:
        if size < step:
            return f"{size:.1f} {unit}"
        size /= step
    return f"{size:.1f} PB"


def get_drives():
    drives = []
    if not is_windows():
        usage = shutil.disk_usage("/")
        drives.append(
            {
                "name": "/",
                "total": usage.total,
                "free": usage.free,
                "used": usage.used,
                "free_percent": round(usage.free / usage.total * 100, 2),
            }
        )
        return drives

    bitmask = ctypes.windll.kernel32.GetLogicalDrives()
    for i in range(26):
        if bitmask & (1 << i):
            letter = chr(65 + i)
            root = f"{letter}:\\"
            drive_type = ctypes.windll.kernel32.GetDriveTypeW(ctypes.c_wchar_p(root))
            if drive_type != 3:
                continue
            usage = shutil.disk_usage(root)
            drives.append(
                {
                    "name": root,
                    "total": usage.total,
                    "free": usage.free,
                    "used": usage.used,
                    "free_percent": round(usage.free / usage.total * 100, 2),
                }
            )
    return drives


def _user_profile_paths():
    home = os.path.expanduser("~")
    local_app_data = os.getenv("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
    return [
        ("Desktop", os.path.join(home, "Desktop")),
        ("Downloads", os.path.join(home, "Downloads")),
        ("Documents", os.path.join(home, "Documents")),
        ("Pictures", os.path.join(home, "Pictures")),
        ("Videos", os.path.join(home, "Videos")),
        ("User Temp", os.path.join(local_app_data, "Temp")),
        ("INET Cache", os.path.join(local_app_data, "Microsoft", "Windows", "INetCache")),
    ]


def get_top_folders(limit=5):
    candidates = []
    for name, path in _user_profile_paths():
        if not os.path.exists(path):
            continue
        size_info = get_dir_size(
            path,
            exclusions=DEFAULT_EXCLUSIONS,
            max_files=50000,
            max_depth=6,
        )
        candidates.append(
            {
                "name": name,
                "path": path,
                "bytes": size_info["bytes"],
                "files": size_info["files"],
                "truncated": size_info["truncated"],
            }
        )
    candidates.sort(key=lambda item: item["bytes"], reverse=True)
    return candidates[:limit]
