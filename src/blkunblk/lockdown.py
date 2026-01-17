"""Lockdown functionality to prevent unblocking for a specified time."""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .config import FOCUS_DIR


LOCKDOWN_FILE = FOCUS_DIR / "lockdown"


class LockdownError(Exception):
    """Error during lockdown operations."""

    pass


def get_midnight_today() -> datetime:
    """Get midnight (end of day) for today."""
    now = datetime.now()
    return now.replace(hour=23, minute=59, second=59, microsecond=999999)


def get_lockdown_end(lockdown_file: Optional[Path] = None) -> Optional[datetime]:
    """Get the lockdown end time, or None if no active lockdown."""
    lockdown_file = lockdown_file or LOCKDOWN_FILE

    if not lockdown_file.exists():
        return None

    try:
        content = lockdown_file.read_text().strip()
        if not content:
            return None

        end_time = datetime.fromisoformat(content)

        # If lockdown has expired, return None
        if end_time <= datetime.now():
            return None

        return end_time
    except (ValueError, OSError):
        return None


def is_locked(lockdown_file: Optional[Path] = None) -> bool:
    """Check if lockdown is currently active."""
    return get_lockdown_end(lockdown_file) is not None


def get_lockdown_remaining(lockdown_file: Optional[Path] = None) -> Optional[timedelta]:
    """Get remaining lockdown time, or None if not locked."""
    end_time = get_lockdown_end(lockdown_file)
    if end_time is None:
        return None
    return end_time - datetime.now()


def set_lockdown(
    hours: float,
    lockdown_file: Optional[Path] = None,
    focus_dir: Optional[Path] = None,
) -> datetime:
    """Set a lockdown for the specified number of hours.

    Args:
        hours: Number of hours to lock (can be float, e.g., 1.5)
        lockdown_file: Path to lockdown file (for testing)
        focus_dir: Path to focus directory (for testing)

    Returns:
        The lockdown end time.

    Raises:
        LockdownError: If hours is invalid or lockdown would extend past midnight.
    """
    lockdown_file = lockdown_file or LOCKDOWN_FILE
    focus_dir = focus_dir or FOCUS_DIR

    if hours <= 0:
        raise LockdownError("Hours must be positive")

    now = datetime.now()
    end_time = now + timedelta(hours=hours)
    midnight = get_midnight_today()

    # Cap at midnight
    if end_time > midnight:
        end_time = midnight

    try:
        focus_dir.mkdir(parents=True, exist_ok=True)
        lockdown_file.write_text(end_time.isoformat())
        return end_time
    except OSError as e:
        raise LockdownError(f"Failed to set lockdown: {e}")


def clear_lockdown(lockdown_file: Optional[Path] = None) -> None:
    """Clear any active lockdown."""
    lockdown_file = lockdown_file or LOCKDOWN_FILE

    try:
        if lockdown_file.exists():
            lockdown_file.unlink()
    except OSError as e:
        raise LockdownError(f"Failed to clear lockdown: {e}")


def format_remaining(remaining: timedelta) -> str:
    """Format remaining time as human-readable string."""
    total_seconds = int(remaining.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
