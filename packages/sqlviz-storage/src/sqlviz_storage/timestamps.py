"""Modification timestamps for writes that must change their persisted row."""

from datetime import datetime, timedelta, timezone


def modification_timestamp(previous: str) -> str:
    """Use microseconds and avoid a no-op write if the clock repeats its value.

    This establishes a row write for conflict detection, not a monotonic revision.
    """
    now = datetime.now(timezone.utc)
    modified_at = now.isoformat(timespec="microseconds")
    if modified_at == previous:
        modified_at = (now + timedelta(microseconds=1)).isoformat(timespec="microseconds")
    return modified_at
