"""DNS cache operations."""

import subprocess


def flush_dns() -> None:
    """Flush the macOS DNS cache."""
    subprocess.run(["dscacheutil", "-flushcache"], check=False, capture_output=True)
    subprocess.run(
        ["killall", "-HUP", "mDNSResponder"], check=False, capture_output=True
    )
