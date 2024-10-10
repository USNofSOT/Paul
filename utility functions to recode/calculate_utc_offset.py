# Function to calculate UTC offset based on provided local time
def calculate_utc_offset(local_time_str: str):
    # Parse the provided local time (expected in HH:MM format)
    try:
        local_time = datetime.strptime(local_time_str, "%H:%M")
    except ValueError:
        return None, "Invalid time format. Please use HH:MM (24-hour format)."

    # Get the current UTC time
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()

    # Adjust the current local time to match the user's provided local time
    adjusted_local_time = local_now.replace(hour=local_time.hour, minute=local_time.minute, second=0, microsecond=0)

    # Calculate the difference between provided local time and UTC time
    utc_offset = adjusted_local_time - utc_now

    # Calculate hours and minutes from the time delta
    hours_offset = int(utc_offset.total_seconds() // 3600)
    minutes_offset = int((utc_offset.total_seconds() % 3600) // 60)

    # Format the offset (e.g., UTC+2 or UTC-5)
    sign = "+" if hours_offset >= 0 else "-"
    formatted_offset = f"UTC{sign}{abs(hours_offset):02d}:{abs(minutes_offset):02d}"

    return formatted_offset, None