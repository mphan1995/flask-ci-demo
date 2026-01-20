import ctypes
import fnmatch
import getpass
import os
import subprocess
import threading
import time

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DATA_DIR = os.path.join(BASE_DIR, "data")
LOCK_FILE = os.path.join(DATA_DIR, "job.lock")

SIMULATION_MODE = os.getenv("SIMULATION", "0").lower() in ("1", "true", "yes")
SAFE_MODE = os.getenv("SAFE_MODE", "1").lower() in ("1", "true", "yes")

DEFAULT_EXCLUSIONS = [
    "*.evtx",
    "*.etl",
    "*.log",
    "*.sys",
    "thumbs.db",
    "desktop.ini",
]

BLOCKED_PATH_FRAGMENTS = [
    os.path.normcase(os.path.join("windows", "winsxs")),
    os.path.normcase(os.path.join("windows", "system32")),
    os.path.normcase("program files"),
    os.path.normcase("program files (x86)"),
]

LOCK_TTL_SECONDS = 6 * 60 * 60


def is_windows():
    return os.name == "nt"


def current_user():
    return getpass.getuser()


def is_admin():
    if not is_windows():
        return False
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _normalize_path(path):
    if not path:
        return ""
    return os.path.normcase(os.path.abspath(os.path.normpath(path)))


def _path_is_blocked(path):
    norm = _normalize_path(path)
    for fragment in BLOCKED_PATH_FRAGMENTS:
        if fragment in norm:
            return True
    return False


def is_path_allowed(path, allowed_roots, safe_mode=True):
    if not path or not allowed_roots:
        return False
    norm = _normalize_path(path)
    if safe_mode and _path_is_blocked(norm):
        return False
    for root in allowed_roots:
        root_norm = _normalize_path(root)
        try:
            common = os.path.commonpath([norm, root_norm])
        except ValueError:
            continue
        if common == root_norm:
            return True
    return False


def validate_path(path, allowed_roots, safe_mode=True):
    if not path:
        return False, "empty_path"
    if not is_path_allowed(path, allowed_roots, safe_mode=safe_mode):
        return False, "path_not_allowed"
    return True, ""


def match_exclusion(name, exclusions):
    for pattern in exclusions:
        if fnmatch.fnmatch(name, pattern):
            return True
    return False


def get_dir_size(path, exclusions=None, max_files=200000, max_depth=8):
    exclusions = exclusions or []
    total = 0
    files = 0
    truncated = False
    errors = []

    base_depth = _normalize_path(path).count(os.sep)

    for root, dirs, file_names in os.walk(path):
        depth = _normalize_path(root).count(os.sep) - base_depth
        if depth > max_depth:
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs if not match_exclusion(d, exclusions)]

        for name in file_names:
            if match_exclusion(name, exclusions):
                continue
            file_path = os.path.join(root, name)
            try:
                total += os.path.getsize(file_path)
                files += 1
            except OSError as exc:
                errors.append(str(exc))

            if files >= max_files:
                truncated = True
                return {
                    "bytes": total,
                    "files": files,
                    "truncated": truncated,
                    "errors": errors,
                }

    return {
        "bytes": total,
        "files": files,
        "truncated": truncated,
        "errors": errors,
    }


def safe_delete_contents(path, allowed_roots, dry_run=False, exclusions=None, max_files=200000):
    exclusions = exclusions or []
    ok, error = validate_path(path, allowed_roots, safe_mode=SAFE_MODE)
    if not ok:
        return {
            "ok": False,
            "error": error,
            "bytes": 0,
            "files_deleted": 0,
            "errors": [],
            "skipped": 0,
        }

    total = 0
    deleted = 0
    skipped = 0
    errors = []

    for root, dirs, file_names in os.walk(path):
        for name in file_names:
            if match_exclusion(name, exclusions):
                skipped += 1
                continue
            file_path = os.path.join(root, name)
            try:
                size = os.path.getsize(file_path)
            except OSError:
                size = 0
            total += size

            if dry_run:
                deleted += 1
                continue

            try:
                os.remove(file_path)
                deleted += 1
            except OSError as exc:
                errors.append(str(exc))

            if deleted >= max_files:
                break
        if deleted >= max_files:
            break

    if not dry_run:
        for root, dirs, _ in os.walk(path, topdown=False):
            for name in dirs:
                dir_path = os.path.join(root, name)
                if not is_path_allowed(dir_path, allowed_roots, safe_mode=SAFE_MODE):
                    continue
                try:
                    os.rmdir(dir_path)
                except OSError:
                    continue

    return {
        "ok": len(errors) == 0,
        "bytes": total,
        "files_deleted": deleted,
        "errors": errors,
        "skipped": skipped,
    }


def safe_delete_file(path, allowed_roots, dry_run=False):
    ok, error = validate_path(path, allowed_roots, safe_mode=SAFE_MODE)
    if not ok:
        return {"ok": False, "error": error}
    if dry_run:
        return {"ok": True, "dry_run": True}
    try:
        os.remove(path)
        return {"ok": True}
    except OSError as exc:
        return {"ok": False, "error": str(exc)}


def _run_subprocess(args, timeout=300):
    try:
        completed = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": exc.stdout or "",
            "stderr": "timeout",
        }
    except Exception as exc:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def run_powershell(command, timeout=300):
    if not is_windows():
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": "powershell_not_available",
        }
    args = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        command,
    ]
    return _run_subprocess(args, timeout=timeout)


def run_cmd(args, timeout=300):
    return _run_subprocess(args, timeout=timeout)


class JobLock:
    def __init__(self, lock_file):
        self.lock_file = lock_file
        self._thread_lock = threading.Lock()
        self._owner_pid = None

    def _cleanup_stale(self):
        if not os.path.exists(self.lock_file):
            return
        try:
            age = time.time() - os.path.getmtime(self.lock_file)
        except OSError:
            return
        if age > LOCK_TTL_SECONDS:
            try:
                os.remove(self.lock_file)
            except OSError:
                return

    def acquire(self):
        os.makedirs(os.path.dirname(self.lock_file), exist_ok=True)
        self._cleanup_stale()
        if not self._thread_lock.acquire(blocking=False):
            return False
        try:
            fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode("ascii"))
            os.close(fd)
            self._owner_pid = os.getpid()
            return True
        except FileExistsError:
            self._thread_lock.release()
            return False
        except OSError:
            self._thread_lock.release()
            return False

    def release(self):
        try:
            if os.path.exists(self.lock_file):
                os.remove(self.lock_file)
        except OSError:
            pass
        self._owner_pid = None
        if self._thread_lock.locked():
            self._thread_lock.release()

    def is_locked(self):
        self._cleanup_stale()
        return self._thread_lock.locked() or os.path.exists(self.lock_file)


job_lock = JobLock(LOCK_FILE)
