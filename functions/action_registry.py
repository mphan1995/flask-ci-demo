from .cleaners import (
    browser_cleaner,
    defender_scan,
    recycle_bin,
    temp_cleaner,
    windows_update_cleaner,
)

ACTIONS = {
    "recycle_bin": {
        "id": "recycle_bin",
        "name": "Empty Recycle Bin",
        "description": "Clear Recycle Bin for all fixed drives.",
        "requires_admin": False,
        "scan": recycle_bin.scan,
        "run": recycle_bin.run,
    },
    "user_temp": {
        "id": "user_temp",
        "name": "Clear User TEMP",
        "description": "Remove files under %TEMP% for current user.",
        "requires_admin": False,
        "scan": temp_cleaner.scan_user_temp,
        "run": temp_cleaner.run_user_temp,
    },
    "windows_temp": {
        "id": "windows_temp",
        "name": "Clear Windows TEMP",
        "description": "Clean C:\\Windows\\Temp (admin required).",
        "requires_admin": True,
        "scan": temp_cleaner.scan_windows_temp,
        "run": temp_cleaner.run_windows_temp,
    },
    "browser_cache": {
        "id": "browser_cache",
        "name": "Clear Browser Cache/Cookies",
        "description": "Remove caches for Chrome, Edge, and Firefox if closed.",
        "requires_admin": False,
        "scan": browser_cleaner.scan_browser_cache,
        "run": browser_cleaner.run_browser_cache,
    },
    "windows_update": {
        "id": "windows_update",
        "name": "Windows Update Cleanup",
        "description": "Use DISM and Delivery Optimization cleanup.",
        "requires_admin": True,
        "scan": windows_update_cleaner.scan_windows_update,
        "run": windows_update_cleaner.run_windows_update,
    },
    "defender_quick_scan": {
        "id": "defender_quick_scan",
        "name": "Windows Defender Quick Scan",
        "description": "Trigger Windows Defender quick scan.",
        "requires_admin": False,
        "scan": defender_scan.scan_defender,
        "run": defender_scan.run_defender,
    },
}


def get_action(action_id):
    return ACTIONS.get(action_id)


def list_actions():
    items = []
    for action in ACTIONS.values():
        items.append(
            {
                "id": action["id"],
                "name": action["name"],
                "description": action["description"],
                "requires_admin": action["requires_admin"],
            }
        )
    return items
