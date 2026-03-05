from datetime import datetime
import time

def get_current_timestamp_str() -> str:
    """Returns the current absolute time formatted as a string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_current_time_seconds() -> float:
    """Returns the current monotonic time in seconds."""
    return time.time()
