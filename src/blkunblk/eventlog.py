"""Event logging to ~/unblk.log."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .config import LOG_FILE


def log_block(log_file: Optional[Path] = None) -> None:
    """Log a block event."""
    log_file = log_file or LOG_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp}; BLOCK\n"

    with open(log_file, "a") as f:
        f.write(entry)


def log_unblock(
    duration: int,
    reason: str,
    domains: Optional[List[str]] = None,
    log_file: Optional[Path] = None,
) -> None:
    """Log an unblock event."""
    log_file = log_file or LOG_FILE
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if domains:
        domains_str = ", ".join(domains)
        entry = f"{timestamp}; UNBLOCK; Duration: {duration} minutes; Reason: {reason}; Specific: {domains_str}\n"
    else:
        entry = f"{timestamp}; UNBLOCK; Duration: {duration} minutes; Reason: {reason}\n"

    with open(log_file, "a") as f:
        f.write(entry)
