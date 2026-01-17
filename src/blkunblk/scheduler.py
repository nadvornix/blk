"""at job scheduling for reblocking."""

import subprocess
import sys
from datetime import datetime, timedelta


class SchedulerError(Exception):
    """Error during job scheduling."""

    pass


def clear_all_at_jobs() -> None:
    """Remove all pending at jobs."""
    try:
        result = subprocess.run(
            ["atq"], capture_output=True, text=True, check=False
        )
        if result.returncode != 0:
            return

        for line in result.stdout.strip().splitlines():
            if line:
                job_id = line.split()[0]
                subprocess.run(["atrm", job_id], check=False, capture_output=True)
    except Exception:
        pass


def schedule_reblock(minutes: int) -> None:
    """Schedule a reblock job to run after the specified minutes."""
    try:
        blk_path = _find_blk_command()
        cmd = f"sudo {blk_path}"

        process = subprocess.Popen(
            ["at", "now", "+", str(minutes), "minutes"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        process.communicate(input=cmd + "\n")
    except Exception as e:
        raise SchedulerError(f"Failed to schedule reblock: {e}")


def _find_blk_command() -> str:
    """Find the blk command path."""
    result = subprocess.run(
        ["which", "blk"], capture_output=True, text=True, check=False
    )
    if result.returncode == 0 and result.stdout.strip():
        return result.stdout.strip()

    return sys.executable.replace("python", "blk")
