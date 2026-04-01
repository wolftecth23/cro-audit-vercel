from datetime import datetime


def calculate_hours(start: datetime, end: datetime) -> float:
    seconds = (end - start).total_seconds()
    return round(seconds / 3600, 2)
