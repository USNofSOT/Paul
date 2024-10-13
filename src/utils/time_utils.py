from datetime import datetime, timezone


def get_time_difference_past(other_time):
    if other_time is None:
        return

    if other_time.tzinfo is None or other_time.utcoffset() is None:
        other_time = other_time.replace(tzinfo=timezone.utc)

    current_time = datetime.now(timezone.utc)
    time_difference = current_time - other_time
    return time_difference


def format_time(time_difference):
    years = time_difference.days // 365
    months = (time_difference.days % 365) // 30
    weeks = (time_difference.days % 365 % 30) // 7
    days = time_difference.days % 365 % 30 % 7
    hours = time_difference.seconds // 3600
    minutes = (time_difference.seconds % 3600) // 60
    seconds = time_difference.seconds % 60

    if years >= 1:
        return f"{years} year{'s' if years > 1 else ''}" + (
            f", {months} month{'s' if months > 1 else ''}" if months > 0 else "")
    elif months >= 1:
        return f"{months} month{'s' if months > 1 else ''}" + (
            f", {weeks} week{'s' if weeks > 1 else ''}" if weeks > 0 else "")
    elif weeks >= 1:
        return f"{weeks} week{'s' if weeks > 1 else ''}" + (
            f", {days} day{'s' if days > 1 else ''}" if days > 0 else "")
    elif days >= 1:
        return f"{days} day{'s' if days > 1 else ''}" + (
            f", {hours} hour{'s' if hours > 1 else ''}" if hours > 0 else "")
    elif hours >= 1:
        return f"{hours} hour{'s' if hours > 1 else ''}" + (
            f", {minutes} minute{'s' if minutes > 1 else ''}" if minutes > 0 else "")
    elif minutes >= 1:
        return f"{minutes} minute{'s' if minutes > 1 else ''}" + (
            f", {seconds} second{'s' if seconds > 1 else ''}" if seconds > 0 else "")
    else:
        return "Just Now"