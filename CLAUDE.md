# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a macOS focus/productivity tool that blocks distracting websites by modifying `/etc/hosts`. It consists of two shell scripts:

- **blk** - Blocks all websites by uncommenting blocked entries in `/etc/hosts`
- **unblk** - Interactive zsh script to temporarily unblock specific sites or all sites for a chosen duration

## Usage

Both scripts require root privileges:

```bash
sudo ./blk      # Block all sites immediately
sudo ./unblk    # Interactive unblock flow (requires gum CLI)
```

## Architecture

### Blocking Mechanism
- Sites are blocked via `/etc/hosts` entries pointing to `0.0.0.0` or `127.0.0.1`
- Lines with `BLOCKME` are standard blocked entries
- Lines with `NEVERBLOCK` are always kept active (never commented out)
- The immutable flag (`chflags uchg`) is toggled to prevent accidental edits

### unblk Flow
1. Asks for reason (min 6 chars)
2. Asks for duration (10/25/60/custom minutes)
3. Asks for domains (specific sites, ALL, or select from recents)
4. Applies friction delays based on duration
5. Comments out matching lines in `/etc/hosts`
6. Schedules reblock via `at` command
7. Logs to `~/unblk.log`

### Key Paths
- `/etc/hosts` - Modified to block/unblock sites
- `~/.focus/recents` - Recently unblocked domains
- `~/unblk.log` - Unblock event log
- `BLK_PATH` in unblk script must point to the blk script location

## Dependencies

- macOS (uses BSD sed, dscacheutil, chflags)
- `gum` CLI for interactive prompts (`brew install gum`)
- `at` daemon for scheduled reblocking
