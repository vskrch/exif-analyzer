"""Application runtime metrics."""

import time

START_TIME = time.time()


def uptime_seconds() -> float:
    """Return seconds since application module was loaded."""
    return round(time.time() - START_TIME, 2)
