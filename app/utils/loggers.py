from datetime import datetime


def log(message: str, *, component: str, worker_id: int | None = None) -> None:
    """
    Print a formatted log message.

    Example:
    - [__main__] message
    - [app.services.corporations_crawler] [Worker #0] message
    """

    if worker_id is not None:
        # Render log messages already include timestamps
        # Use commented out print statement for local crawler run to see timestamps in logs
        # timestamp = datetime.now().strftime("%H:%M:%S")
        # print(f"[{timestamp}] [{component}] [Worker #{worker_id}] {message}")
        print(f"[{component}] [Worker #{worker_id}] {message}")
    else:
        print(f"[{component}] {message}")


def format_duration(start_time: datetime, end_time: datetime) -> str:
    """
    Format the duration between start_time and end_time as HH:MM:SS.
    """

    # Example:
    # start_time = 10:00:00
    # end_time = 11:01:11
    # duration = 1 hour, 1 minute, 11 seconds
    duration = end_time - start_time

    # Convert duration into total seconds.
    # Example:
    # 1 hour = 3600 seconds
    # 1 minute = 60 seconds
    # 11 seconds = 11 seconds
    # total_seconds = 3600 + 60 + 11 = 3671
    total_seconds = int(duration.total_seconds())

    # Get the number of full hours.
    # Example:
    # 3671 // 3600 = 1
    hours = total_seconds // 3600

    # Get the leftover seconds after removing full hours.
    # Example:
    # 3671 % 3600 = 71
    remaining_seconds = total_seconds % 3600

    # Get the number of full minutes from the leftover seconds.
    # Example:
    # 71 // 60 = 1
    minutes = remaining_seconds // 60

    # Get the leftover seconds after removing full minutes.
    # Example:
    # 71 % 60 = 11
    seconds = remaining_seconds % 60

    # Format each value as 2 digits.
    # Example:
    # hours = 1    -> "01"
    # minutes = 1  -> "01"
    # seconds = 11 -> "11"
    # Result: "01:01:11"
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
