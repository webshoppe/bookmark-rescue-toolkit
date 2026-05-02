"""
utils.py - Bookmark Rescue Toolkit
====================================
Shared helpers used by both converter engines.
Centralised here to avoid duplication and ensure consistent behaviour.
"""

from datetime import datetime


def get_human_date(unix_time: int) -> str:
    """Convert a Unix timestamp to a readable date string.

    Returns 'Unknown Date' for zero, negative, or out-of-range values so
    callers never have to guard against a formatting exception.
    """
    if not unix_time or unix_time <= 0:
        return "Unknown Date"
    try:
        return datetime.fromtimestamp(unix_time).strftime("%B %d, %Y")
    except (OSError, OverflowError, ValueError):
        return "Unknown Date"
