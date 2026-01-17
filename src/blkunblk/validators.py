"""Input validation for blkunblk."""

from typing import List


MIN_PATTERN_LENGTH = 4


def is_valid_pattern(pattern: str) -> bool:
    """Validate a domain pattern (grep-style matching)."""
    return len(pattern) >= MIN_PATTERN_LENGTH


def validate_patterns(patterns: List[str]) -> List[str]:
    """Validate a list of patterns, raising ValueError for invalid ones."""
    invalid = [p for p in patterns if not is_valid_pattern(p)]
    if invalid:
        raise ValueError(f"Pattern must be at least {MIN_PATTERN_LENGTH} chars: {', '.join(invalid)}")
    return patterns


def validate_duration(value: str) -> int:
    """Validate duration string, returning integer minutes."""
    from .config import MIN_DURATION, MAX_DURATION

    try:
        minutes = int(value.strip())
    except ValueError:
        raise ValueError("Duration must be a number")

    if minutes < MIN_DURATION or minutes > MAX_DURATION:
        raise ValueError(f"Duration must be {MIN_DURATION}-{MAX_DURATION} minutes")

    return minutes


def validate_reason(reason: str) -> str:
    """Validate reason string."""
    from .config import MIN_REASON_LENGTH

    reason = reason.strip()
    if len(reason) < MIN_REASON_LENGTH:
        raise ValueError(f"Reason must be at least {MIN_REASON_LENGTH} characters")
    return reason
