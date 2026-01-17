"""CLI entry points for blk and unblk commands."""

import os
import sys
from typing import List

from rich.console import Console

from .config import HOSTS_FILE
from .dns import flush_dns
from .eventlog import log_block, log_unblock
from .friction import (
    confirm_window,
    get_all_wait_seconds,
    get_specific_wait_seconds,
    wait_with_spinner,
)
from .hosts import (
    HostsError,
    block_all,
    remove_immutable_flag,
    set_immutable_flag,
    unblock_all,
    unblock_domains,
)
from .lockdown import (
    LockdownError,
    format_remaining,
    get_lockdown_remaining,
    is_locked,
    set_lockdown,
)
from .prompts import PromptCancelled, prompt_domains, prompt_duration, prompt_reason
from .recents import RecentsError, update_recents
from .scheduler import clear_all_at_jobs, schedule_reblock

console = Console()


def check_root() -> None:
    """Ensure running as root."""
    if os.geteuid() != 0:
        console.print("[red]Please run as root (sudo)[/red]")
        sys.exit(1)


def check_platform() -> None:
    """Ensure running on a supported platform."""
    supported = ["darwin", "linux", "win32"]
    if sys.platform not in supported:
        console.print(f"[red]Unsupported platform: {sys.platform}[/red]")
        sys.exit(1)


def get_blocked_domains() -> List[str]:
    """Get list of currently blocked domains from hosts file."""
    blocked = []
    try:
        content = HOSTS_FILE.read_text()
        for line in content.splitlines():
            # Active BLOCKME lines (not commented)
            if "BLOCKME" in line and not line.lstrip().startswith("#"):
                # Extract domain from line like "0.0.0.0 facebook.com # BLOCKME"
                parts = line.split()
                if len(parts) >= 2:
                    blocked.append(parts[1])
    except OSError:
        pass
    return blocked


def get_unblocked_domains() -> List[str]:
    """Get list of currently unblocked domains from hosts file."""
    unblocked = []
    try:
        content = HOSTS_FILE.read_text()
        for line in content.splitlines():
            # Commented BLOCKME lines
            if "BLOCKME" in line and line.lstrip().startswith("#"):
                # Extract domain from line like "# 0.0.0.0 facebook.com # BLOCKME"
                parts = line.split()
                if len(parts) >= 3:
                    unblocked.append(parts[2])
    except OSError:
        pass
    return unblocked


def blk_status() -> None:
    """Show current blocking status."""
    check_platform()

    # Check lockdown status
    remaining = get_lockdown_remaining()
    if remaining:
        console.print(f"[red]LOCKED[/red] for {format_remaining(remaining)}")

    # Check unblocked sites
    unblocked = get_unblocked_domains()

    if not unblocked:
        console.print("All blocked")
    elif len(unblocked) <= 3:
        console.print(f"Unblocked: {', '.join(unblocked)}")
    else:
        console.print("Unblocked: many")


def blk_lock(hours_str: str) -> None:
    """Lock unblocking for specified hours."""
    check_platform()
    check_root()

    try:
        hours = float(hours_str)
    except ValueError:
        console.print("[red]Invalid hours. Use a number like 2 or 1.5[/red]")
        sys.exit(1)

    if hours <= 0:
        console.print("[red]Hours must be positive[/red]")
        sys.exit(1)

    try:
        end_time = set_lockdown(hours)
        console.print(
            f"[green]Locked until {end_time.strftime('%H:%M')}[/green]"
        )
        console.print("[dim]unblk will be disabled until then[/dim]")
    except LockdownError as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def blk_block() -> None:
    """Block all websites."""
    check_platform()
    check_root()

    try:
        remove_immutable_flag()

        block_all()

        flush_dns()

        clear_all_at_jobs()

        log_block()

        set_immutable_flag()

        console.print("[green]Websites blocked successfully.[/green]")
        console.print("DNS cache flushed.")

    except HostsError as e:
        console.print(f"[red]Error: {e}[/red]")
        set_immutable_flag()
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        set_immutable_flag()
        sys.exit(1)


def blk_main() -> None:
    """Entry point for blk command - handles subcommands."""
    args = sys.argv[1:]

    if not args:
        # Default: block all
        blk_block()
        return

    cmd = args[0].lower()

    if cmd == "status":
        blk_status()
    elif cmd == "lock":
        if len(args) < 2:
            console.print("[red]Usage: blk lock <hours>[/red]")
            console.print("Example: blk lock 2    (lock for 2 hours)")
            console.print("Example: blk lock 0.5  (lock for 30 minutes)")
            sys.exit(1)
        blk_lock(args[1])
    else:
        console.print(f"[red]Unknown command: {cmd}[/red]")
        console.print("Usage: blk [status|lock <hours>]")
        sys.exit(1)


def unblk_main() -> None:
    """Entry point for unblk command - interactive website unblocker."""
    check_platform()
    check_root()

    # Check for lockdown
    remaining = get_lockdown_remaining()
    if remaining:
        console.print(f"[red]Locked for {format_remaining(remaining)}[/red]")
        console.print("[dim]Use 'blk status' to check lockdown[/dim]")
        sys.exit(1)

    try:
        remove_immutable_flag()

        block_all()

        reason = prompt_reason()

        duration = prompt_duration()

        is_all, domains = prompt_domains()

        if is_all:
            wait_seconds = get_all_wait_seconds()
            wait_with_spinner(wait_seconds, "Preparing ALL... waiting")

            if not confirm_window(10):
                console.print("[yellow]Timed out. Aborting.[/yellow]")
                set_immutable_flag()
                sys.exit(1)
        else:
            wait_seconds = get_specific_wait_seconds(duration)
            if wait_seconds > 0:
                wait_with_spinner(wait_seconds, "Waiting")

        if is_all:
            unblock_all()
        else:
            unblock_domains(domains)

        flush_dns()

        if is_all:
            log_unblock(duration, reason)
        else:
            log_unblock(duration, reason, domains)

            try:
                update_recents(domains)
            except RecentsError as e:
                console.print(f"[yellow]Warning: {e}[/yellow]")

        schedule_reblock(duration)

        set_immutable_flag()

        if is_all:
            console.print(f"[green]Done: ALL for {duration}m[/green]")
        else:
            domains_str = ", ".join(domains)
            console.print(f"[green]Done: {domains_str} for {duration}m[/green]")

    except PromptCancelled as e:
        console.print(f"[yellow]{e}[/yellow]")
        set_immutable_flag()
        sys.exit(1)
    except HostsError as e:
        console.print(f"[red]Error: {e}[/red]")
        set_immutable_flag()
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled[/yellow]")
        set_immutable_flag()
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "blk":
        blk_main()
    else:
        unblk_main()
