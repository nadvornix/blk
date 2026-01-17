"""Recent domains management with proper error handling.

This module fixes the original bug where update_recents() used `|| true` to mask
errors. If file operations failed silently, the script could exit before printing
the success message. Now we use explicit exceptions so failures are visible.
"""

from pathlib import Path
from typing import List, Optional

from .config import FOCUS_DIR, RECENTS_FILE, RECENTS_MAX


class RecentsError(Exception):
    """Error during recents file operations."""

    pass


def ensure_recents_dir(
    focus_dir: Optional[Path] = None, recents_file: Optional[Path] = None
) -> None:
    """Ensure the focus directory and recents file exist."""
    focus_dir = focus_dir or FOCUS_DIR
    recents_file = recents_file or RECENTS_FILE
    try:
        focus_dir.mkdir(parents=True, exist_ok=True)
        if not recents_file.exists():
            recents_file.touch()
    except PermissionError as e:
        raise RecentsError(f"Cannot create focus directory: {e}")
    except Exception as e:
        raise RecentsError(f"Failed to initialize recents: {e}")


def list_recents(
    focus_dir: Optional[Path] = None, recents_file: Optional[Path] = None
) -> List[str]:
    """Get list of recently unblocked domains."""
    focus_dir = focus_dir or FOCUS_DIR
    recents_file = recents_file or RECENTS_FILE
    try:
        ensure_recents_dir(focus_dir, recents_file)
        content = recents_file.read_text()
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        return lines[:RECENTS_MAX]
    except RecentsError:
        raise
    except Exception as e:
        raise RecentsError(f"Failed to read recents: {e}")


def update_recents(
    domains: List[str],
    focus_dir: Optional[Path] = None,
    recents_file: Optional[Path] = None,
) -> None:
    """Update the recents file with new domains.

    This is the key bug fix: instead of silently ignoring errors with `|| true`,
    we now raise explicit exceptions. The caller (cli.py) catches these and
    warns the user but continues, ensuring the success message is always printed.
    """
    focus_dir = focus_dir or FOCUS_DIR
    recents_file = recents_file or RECENTS_FILE
    try:
        ensure_recents_dir(focus_dir, recents_file)

        existing = []
        if recents_file.exists():
            content = recents_file.read_text()
            existing = [line.strip() for line in content.splitlines() if line.strip()]

        for domain in reversed(domains):
            existing = [d for d in existing if d != domain]
            existing.insert(0, domain)

        existing = existing[:RECENTS_MAX]

        recents_file.write_text("\n".join(existing) + "\n")
    except PermissionError as e:
        raise RecentsError(f"Cannot write recents file: {e}")
    except Exception as e:
        raise RecentsError(f"Failed to update recents: {e}")
