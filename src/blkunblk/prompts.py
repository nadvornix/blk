"""TUI prompts using questionary."""

from typing import List, Optional, Tuple, Union

import questionary
from rich.console import Console

from .config import DURATION_CHOICES, MAX_DURATION, MIN_DURATION, MIN_REASON_LENGTH
from .recents import RecentsError, list_recents
from .validators import is_valid_pattern, MIN_PATTERN_LENGTH

console = Console()


class PromptCancelled(Exception):
    """User cancelled the prompt."""

    pass


def prompt_reason() -> str:
    """Prompt for reason with minimum length validation."""
    while True:
        reason: Optional[str] = questionary.text(
            f"Reason (min {MIN_REASON_LENGTH} chars):",
            validate=lambda x: len(x.strip()) >= MIN_REASON_LENGTH
            or f"Must be at least {MIN_REASON_LENGTH} characters",
        ).ask()

        if reason is None:
            raise PromptCancelled("Reason required")

        reason_stripped = reason.strip()
        if len(reason_stripped) >= MIN_REASON_LENGTH:
            return reason_stripped


def prompt_duration() -> int:
    """Prompt for duration and return minutes as integer."""
    choice = questionary.select(
        "Duration (minutes):",
        choices=DURATION_CHOICES,
    ).ask()

    if choice is None:
        raise PromptCancelled("Duration required")

    if choice == "Custom":
        custom = questionary.text(
            f"Enter minutes ({MIN_DURATION}-{MAX_DURATION}):",
            validate=lambda x: _validate_custom_duration(x),
        ).ask()

        if custom is None:
            raise PromptCancelled("Duration required")

        return int(custom.strip())
    else:
        return int(choice)


def _validate_custom_duration(value: str) -> Union[bool, str]:
    """Validate custom duration input."""
    try:
        minutes = int(value.strip())
        if MIN_DURATION <= minutes <= MAX_DURATION:
            return True
        return f"Must be {MIN_DURATION}-{MAX_DURATION}"
    except ValueError:
        return "Enter a valid number"


def prompt_domains() -> Tuple[bool, List[str]]:
    """Prompt for domains to unblock.

    Returns:
        Tuple of (is_all, domains_list)
        - If is_all is True, domains_list is empty
        - If is_all is False, domains_list contains the domains
    """
    initial = questionary.text(
        "What to unblock? (ALL or space-separated domains, empty for recents):"
    ).ask()

    if initial is None:
        raise PromptCancelled("Cancelled")

    initial = initial.strip()

    if initial.lower() == "all":
        return True, []

    if initial:
        domains = initial.split()
        _validate_pattern_list(domains)
        return False, domains

    return _prompt_from_recents()


def _prompt_from_recents() -> Tuple[bool, List[str]]:
    """Show recents picker or manual entry if no recents."""
    try:
        recents = list_recents()
    except RecentsError:
        recents = []

    if not recents:
        return _prompt_manual_domains("No recents yet. Enter space-separated domains:")

    choices = ["Type domains manually..."] + recents

    selected = questionary.checkbox(
        "Select domains (space to toggle, enter to confirm):",
        choices=choices,
    ).ask()

    if selected is None:
        raise PromptCancelled("No selection")

    if not selected:
        raise PromptCancelled("No domains provided")

    if "Type domains manually..." in selected:
        return _prompt_manual_domains("Enter space-separated domains:")

    _validate_pattern_list(selected)
    return False, selected


def _prompt_manual_domains(message: str) -> Tuple[bool, List[str]]:
    """Prompt for manual domain entry."""
    manual = questionary.text(message).ask()

    if manual is None or not manual.strip():
        raise PromptCancelled("No domains provided")

    patterns = manual.strip().split()
    _validate_pattern_list(patterns)
    return False, patterns


def _validate_pattern_list(patterns: List[str]) -> None:
    """Validate a list of patterns, raising PromptCancelled for invalid ones."""
    for pattern in patterns:
        if not is_valid_pattern(pattern):
            console.print(f"[red]Pattern must be at least {MIN_PATTERN_LENGTH} chars: {pattern}[/red]")
            raise PromptCancelled(f"Invalid pattern: {pattern}")
