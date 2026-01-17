"""Operations on /etc/hosts file."""

import re
import subprocess
import sys
from pathlib import Path
from typing import List

from .config import HOSTS_FILE


class HostsError(Exception):
    """Error during hosts file operations."""

    pass


def remove_immutable_flag(path: Path = HOSTS_FILE) -> None:
    """Remove the immutable flag from the hosts file."""
    try:
        if sys.platform == "darwin":
            subprocess.run(
                ["chflags", "nouchg", str(path)],
                check=False,
                capture_output=True,
            )
        elif sys.platform == "linux":
            subprocess.run(
                ["chattr", "-i", str(path)],
                check=False,
                capture_output=True,
            )
        # Windows: no equivalent, skip
    except Exception as e:
        raise HostsError(f"Failed to remove immutable flag: {e}")


def set_immutable_flag(path: Path = HOSTS_FILE) -> None:
    """Set the immutable flag on the hosts file."""
    try:
        if sys.platform == "darwin":
            subprocess.run(
                ["chflags", "uchg", str(path)],
                check=False,
                capture_output=True,
            )
        elif sys.platform == "linux":
            subprocess.run(
                ["chattr", "+i", str(path)],
                check=False,
                capture_output=True,
            )
        # Windows: no equivalent, skip
    except Exception as e:
        raise HostsError(f"Failed to set immutable flag: {e}")


def normalize_hosts(path: Path = HOSTS_FILE) -> None:
    """Uncomment all lines except those containing NEVERBLOCK."""
    try:
        content = path.read_text()
        lines = content.splitlines()
        new_lines = []

        for line in lines:
            if "NEVERBLOCK" in line:
                new_lines.append(line)
            else:
                new_lines.append(re.sub(r"^#*", "", line))

        path.write_text("\n".join(new_lines) + "\n")
    except Exception as e:
        raise HostsError(f"Failed to normalize hosts file: {e}")


def normalize_comment_style(path: Path = HOSTS_FILE) -> None:
    """Normalize comment style: remove leading spaces, collapse multiple # to single #."""
    try:
        content = path.read_text()
        lines = content.splitlines()
        new_lines = []

        for line in lines:
            line = line.lstrip()
            line = re.sub(r"^#+", "#", line)
            line = re.sub(r"^# +", "#", line)
            new_lines.append(line)

        path.write_text("\n".join(new_lines) + "\n")
    except Exception as e:
        raise HostsError(f"Failed to normalize comment style: {e}")


def block_all(path: Path = HOSTS_FILE) -> None:
    """Uncomment all lines except those containing NEVERBLOCK (blocking websites)."""
    normalize_hosts(path)
    normalize_comment_style(path)


def unblock_all(path: Path = HOSTS_FILE) -> None:
    """Comment out all lines with BLOCKME except those with NEVERBLOCK."""
    try:
        content = path.read_text()
        lines = content.splitlines()
        new_lines = []

        for line in lines:
            if "NEVERBLOCK" in line:
                new_lines.append(line)
            elif "BLOCKME" in line and not line.lstrip().startswith("#"):
                new_lines.append("# " + line)
            else:
                new_lines.append(line)

        path.write_text("\n".join(new_lines) + "\n")
    except Exception as e:
        raise HostsError(f"Failed to unblock all sites: {e}")


def unblock_domains(domains: List[str], path: Path = HOSTS_FILE) -> None:
    """Comment out lines containing specific domains (unblocking them)."""
    try:
        content = path.read_text()
        lines = content.splitlines()
        new_lines = []

        for line in lines:
            if "NEVERBLOCK" in line:
                new_lines.append(line)
            elif line.lstrip().startswith("#"):
                new_lines.append(line)
            elif any(domain in line for domain in domains):
                new_lines.append("# " + line)
            else:
                new_lines.append(line)

        path.write_text("\n".join(new_lines) + "\n")
    except Exception as e:
        raise HostsError(f"Failed to unblock domains: {e}")
