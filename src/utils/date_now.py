"""Date manipulation utilities module."""

from datetime import datetime, timezone


def get_utc_now() -> datetime:
    """Return the current date and time in UTC.

    :return: Current date and time in UTC
    :rtype: datetime
    """
    return datetime.now(timezone.utc)
