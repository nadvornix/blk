# blk

A focus/productivity tool that blocks distracting websites by modifying `/etc/hosts`.

## Features

- **blk** - Block all configured sites instantly
- **unblk** - Interactive unblocking with friction (reason required, delays, time limits)
- **blk status** - Show currently unblocked sites
- **blk lock \<hours\>** - Prevent unblocking for specified hours

## Installation

Requires Python 3.8+. Supports macOS and Linux.

On Linux, you may need to install `at` for scheduled reblocking:
```bash
sudo apt install at  # Debian/Ubuntu
sudo yum install at  # RHEL/CentOS
```

```bash
# Install with uv (recommended)
uv tool install git+https://github.com/nadvornix/blk

# Or with pipx
pipx install git+https://github.com/nadvornix/blk
```

## Usage

```bash
# Block all sites
sudo blk

# Check status
blk status

# Interactively unblock sites for a duration
sudo unblk

# Lock unblocking for 2 hours
sudo blk lock 2
```

## How it works

1. Sites are blocked via `/etc/hosts` entries pointing to `0.0.0.0`
2. Lines marked with `# BLOCKME` are managed by this tool
3. Lines with `# NEVERBLOCK` are always kept active
4. The immutable flag prevents accidental edits
5. Unblocking schedules automatic reblocking via `at`

## Setup

Add entries to `/etc/hosts` like:

```
0.0.0.0    youtube.com # BLOCKME
0.0.0.0    www.youtube.com # BLOCKME
0.0.0.0    twitter.com # BLOCKME
0.0.0.0    importantsite.com # NEVERBLOCK
```

## unblk flow

1. Asks for reason (min 6 chars) - forces you to think
2. Asks for duration (10/25/60/custom minutes)
3. Asks for patterns to unblock (e.g., "youtube" matches all youtube entries)
4. Applies friction delays based on duration
5. Schedules automatic reblocking

## License

MIT
