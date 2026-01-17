"""Friction delays to add intentional waiting periods."""

import random
import time

from rich.console import Console

console = Console()


def get_specific_wait_seconds(duration_minutes: int) -> int:
    """Calculate wait time for specific domain unblock based on duration.

    Matching the original shell script:
    - <= 20 min: 0-2s
    - <= 60 min: 5-12s
    - <= 180 min: 15-45s
    - > 180 min: 30-90s
    """
    if duration_minutes <= 20:
        return random.randint(0, 2)
    elif duration_minutes <= 60:
        return random.randint(5, 12)
    elif duration_minutes <= 180:
        return random.randint(15, 45)
    else:
        return random.randint(30, 90)


def get_all_wait_seconds() -> int:
    """Calculate wait time for ALL unblock: 30-90 seconds."""
    return random.randint(30, 90)


def wait_with_spinner(seconds: int, message: str = "Waiting") -> None:
    """Wait for specified seconds with a spinner."""
    if seconds <= 0:
        return

    with console.status(f"[bold blue]{message} {seconds}s...[/bold blue]"):
        time.sleep(seconds)


def confirm_window(timeout_seconds: int = 10) -> bool:
    """Wait for Enter key within timeout. Returns True if confirmed."""
    console.print(f"Press Enter within {timeout_seconds}s to confirm...")

    import select
    import sys

    ready, _, _ = select.select([sys.stdin], [], [], timeout_seconds)
    if ready:
        sys.stdin.readline()
        return True
    return False
