"""Configuration constants for blkunblk."""

import os
import sys
from pathlib import Path


def _get_path(env_var: str, default: Path) -> Path:
    """Get a path from environment variable or use default."""
    value = os.environ.get(env_var)
    if value:
        return Path(value)
    return default


def _get_hosts_file() -> Path:
    """Get the hosts file path for the current platform."""
    if sys.platform == "win32":
        return Path(r"C:\Windows\System32\drivers\etc\hosts")
    return Path("/etc/hosts")


HOSTS_FILE = _get_path("BLKUNBLK_HOSTS_FILE", _get_hosts_file())
FOCUS_DIR = _get_path("BLKUNBLK_FOCUS_DIR", Path.home() / ".focus")
RECENTS_FILE = FOCUS_DIR / "recents"
LOG_FILE = _get_path("BLKUNBLK_LOG_FILE", Path.home() / "unblk.log")

RECENTS_MAX = 3
MIN_DURATION = 1
MAX_DURATION = 480
MIN_REASON_LENGTH = 6

DURATION_CHOICES = ["10", "25", "60", "Custom"]
