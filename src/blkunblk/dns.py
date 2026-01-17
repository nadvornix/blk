"""DNS cache operations."""

import subprocess
import sys


def flush_dns() -> None:
    """Flush the DNS cache."""
    if sys.platform == "darwin":
        subprocess.run(["dscacheutil", "-flushcache"], check=False, capture_output=True)
        subprocess.run(
            ["killall", "-HUP", "mDNSResponder"], check=False, capture_output=True
        )
    else:  # linux
        # Try systemd-resolve first, then resolvectl
        result = subprocess.run(
            ["systemd-resolve", "--flush-caches"], check=False, capture_output=True
        )
        if result.returncode != 0:
            subprocess.run(
                ["resolvectl", "flush-caches"], check=False, capture_output=True
            )
