import datetime
from datetime import timezone

def utc_time_now():
    return datetime.datetime.now(datetime.UTC)

def get_time_difference(time_a: datetime, time_b: datetime) -> datetime or None:
    if time_b is None:
        return

    if time_b.tzinfo is None or time_b.utcoffset() is None:
        time_b = time_b.replace(tzinfo=timezone.utc)

    if time_a.tzinfo is None or time_a.utcoffset() is None:
        time_a = time_a.replace(tzinfo=timezone.utc)

    time_difference = time_a - time_b
    return time_difference


def get_time_difference_past(other_time):
    return get_time_difference(utc_time_now(), other_time)


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
