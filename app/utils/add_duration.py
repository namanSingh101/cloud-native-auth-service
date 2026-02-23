from datetime import datetime, timedelta, timezone

def add_duration(duration_str: str) -> str:

    """
    Accepts strings like:
    "10 seconds", "1 minute", "2 hours", "3 days"
    Returns: current UTC time + duration
    """
     
    now = datetime.now(timezone.utc)

    value, unit = duration_str.split()
    value = int(value)

    unit = unit.lower()

    match unit:
        case "second" | "seconds":
            delta = timedelta(seconds=value)
        case "minute" | "minutes":
            delta = timedelta(minutes=value)
        case "hour" | "hours":
            delta = timedelta(hours=value)
        case "day" | "days":
            delta = timedelta(days=value)
        case _:
            raise ValueError("Unsupported time unit")
    total_time = now + delta
    return total_time.strftime("%Y-%m-%d %H:%M:%S")

   