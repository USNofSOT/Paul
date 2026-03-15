from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone
from math import ceil
from typing import Any

from matplotlib import pyplot as plt

from src.config.pocket_watch import (
    POCKET_WATCH_DEFAULT_DAYS,
    POCKET_WATCH_MAX_DAYS,
    POCKET_WATCH_MIN_ACTIVE_WEEKS,
    POCKET_WATCH_MIN_ATTENDED_VOYAGES,
    POCKET_WATCH_MIN_DAYS,
)
from src.utils.image_cache import render_matplotlib_plot_to_png

WEEKDAY_LABELS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")
UTC_OFFSET_PATTERN = re.compile(
    r"UTC(?P<sign>[+-])(?P<hours>\d{1,2})(?::(?P<minutes>\d{2}))?"
)


@dataclass(frozen=True)
class PocketWatchThresholds:
    default_days: int = POCKET_WATCH_DEFAULT_DAYS
    min_days: int = POCKET_WATCH_MIN_DAYS
    max_days: int = POCKET_WATCH_MAX_DAYS
    min_attended_voyages: int = POCKET_WATCH_MIN_ATTENDED_VOYAGES
    min_active_weeks: int = POCKET_WATCH_MIN_ACTIVE_WEEKS


DEFAULT_POCKET_WATCH_THRESHOLDS = PocketWatchThresholds()


@dataclass(frozen=True)
class PocketWatchAnalysis:
    timezone_label: str
    window_start: datetime
    window_end: datetime
    total_voyages: int
    total_hosted: int
    active_weeks: int
    total_weeks: int
    average_voyages_per_week: float
    average_voyages_per_active_week: float
    first_voyage_at: datetime
    last_voyage_at: datetime
    most_active_hour: int
    most_active_hour_count: int
    most_active_weekday: int
    most_active_weekday_count: int
    weekly_labels: tuple[str, ...]
    weekly_attended_counts: tuple[int, ...]
    weekly_hosted_counts: tuple[int, ...]
    weekday_counts: tuple[int, ...]
    hourly_counts: tuple[int, ...]

    @property
    def most_active_hour_label(self) -> str:
        end_hour = (self.most_active_hour + 1) % 24
        return f"{self.most_active_hour:02d}:00-{end_hour:02d}:00"

    @property
    def most_active_weekday_label(self) -> str:
        return WEEKDAY_LABELS[self.most_active_weekday]

    @property
    def hosted_activity_present(self) -> bool:
        return self.total_hosted > 0

    def cache_payload(
            self,
            *,
            target_id: int,
            days: int,
            display_name: str,
    ) -> dict[str, Any]:
        return {
            "target_id": target_id,
            "display_name": display_name,
            "days": days,
            "timezone_label": self.timezone_label,
            "window_start_date": self.window_start.date().isoformat(),
            "window_end_date": self.window_end.date().isoformat(),
            "weekly_labels": self.weekly_labels,
            "weekly_attended_counts": self.weekly_attended_counts,
            "weekly_hosted_counts": self.weekly_hosted_counts,
            "weekday_counts": self.weekday_counts,
            "hourly_counts": self.hourly_counts,
        }


class PocketWatchError(ValueError):
    """Base error for pocket watch analytics."""


class PocketWatchInsufficientDataError(PocketWatchError):
    """Raised when there is not enough activity to produce a reliable view."""


def parse_timezone_label(timezone_value: str | None) -> tuple[timezone, str]:
    if not timezone_value:
        return UTC, "UTC"

    normalized = timezone_value.strip()
    normalized = normalized.replace("\u00c2", "")
    normalized = normalized.replace("\u00b1", "+")
    match = UTC_OFFSET_PATTERN.search(normalized)
    if not match:
        return UTC, "UTC"

    sign = -1 if match.group("sign") == "-" else 1
    hours = int(match.group("hours"))
    minutes = int(match.group("minutes") or 0)
    total_minutes = sign * ((hours * 60) + minutes)
    return timezone(timedelta(minutes=total_minutes)), timezone_value.strip()


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def start_of_week(day: date) -> date:
    return day - timedelta(days=day.weekday())


def validate_days(
        days: int,
        thresholds: PocketWatchThresholds = DEFAULT_POCKET_WATCH_THRESHOLDS,
) -> None:
    if days < thresholds.min_days or days > thresholds.max_days:
        raise PocketWatchError(
            f"Days must be between {thresholds.min_days} and {thresholds.max_days}."
        )


def _build_week_range(window_start: datetime, window_end: datetime) -> list[date]:
    current = start_of_week(window_start.date())
    final_week = start_of_week(window_end.date())
    weeks: list[date] = []
    while current <= final_week:
        weeks.append(current)
        current += timedelta(days=7)
    return weeks


def _build_weekly_tick_positions(total_labels: int) -> list[int]:
    if total_labels <= 0:
        return []

    if total_labels <= 12:
        return list(range(total_labels))

    step = ceil(total_labels / 12)
    tick_positions = list(range(0, total_labels, step))
    last_index = total_labels - 1
    if tick_positions[-1] != last_index:
        tick_positions.append(last_index)
    return tick_positions


def _render_insufficient_data_message(
        *,
        total_voyages: int,
        active_weeks: int,
        thresholds: PocketWatchThresholds,
) -> str:
    reasons = []
    if total_voyages < thresholds.min_attended_voyages:
        reasons.append(
            "Attended voyages in range: "
            f"{total_voyages}/{thresholds.min_attended_voyages}"
        )
    if active_weeks < thresholds.min_active_weeks:
        reasons.append(
            f"Active weeks in range: {active_weeks}/{thresholds.min_active_weeks}"
        )

    reason_text = "\n".join(f"- {reason}" for reason in reasons)
    return (
        "Not enough voyage data has been gathered for a reliable pocket watch view.\n"
        f"{reason_text}\n"
        f"Try a larger range between {thresholds.min_days} and {thresholds.max_days} "
        "days, or wait for more voyage activity."
    )


def analyze_pocket_watch_activity(
        attended_voyages: list[Any],
        hosted_entries: list[Any] | None = None,
        *,
        days: int = POCKET_WATCH_DEFAULT_DAYS,
        timezone_value: str | None = None,
        thresholds: PocketWatchThresholds = DEFAULT_POCKET_WATCH_THRESHOLDS,
        now: datetime | None = None,
) -> PocketWatchAnalysis:
    validate_days(days, thresholds)

    if not attended_voyages:
        raise PocketWatchInsufficientDataError(
            "No attended voyages were found in the selected time range."
        )

    resolved_now = ensure_utc(now or datetime.now(UTC))
    local_timezone, timezone_label = parse_timezone_label(timezone_value)
    window_end = resolved_now.astimezone(local_timezone)
    window_start = (resolved_now - timedelta(days=days)).astimezone(local_timezone)

    local_attended_times = [
        ensure_utc(voyage.log_time).astimezone(local_timezone)
        for voyage in attended_voyages
    ]
    local_hosted_times = [
        ensure_utc(entry.log_time).astimezone(local_timezone)
        for entry in (hosted_entries or [])
    ]

    week_range = _build_week_range(window_start, window_end)
    weekly_attended_counter = Counter(
        start_of_week(local_time.date()) for local_time in local_attended_times
    )
    weekly_hosted_counter = Counter(
        start_of_week(local_time.date()) for local_time in local_hosted_times
    )
    weekly_attended_counts = tuple(
        weekly_attended_counter[week] for week in week_range
    )
    weekly_hosted_counts = tuple(weekly_hosted_counter[week] for week in week_range)
    active_weeks = sum(1 for count in weekly_attended_counts if count > 0)

    if (
            len(local_attended_times) < thresholds.min_attended_voyages
            or active_weeks < thresholds.min_active_weeks
    ):
        raise PocketWatchInsufficientDataError(
            _render_insufficient_data_message(
                total_voyages=len(local_attended_times),
                active_weeks=active_weeks,
                thresholds=thresholds,
            )
        )

    weekday_counter = Counter(
        local_time.weekday() for local_time in local_attended_times
    )
    weekday_counts = tuple(weekday_counter.get(index, 0) for index in range(7))

    hourly_counter = Counter(local_time.hour for local_time in local_attended_times)
    hourly_counts = tuple(hourly_counter.get(index, 0) for index in range(24))

    most_active_hour, most_active_hour_count = max(
        enumerate(hourly_counts),
        key=lambda item: (item[1], -item[0]),
    )
    most_active_weekday, most_active_weekday_count = max(
        enumerate(weekday_counts),
        key=lambda item: (item[1], -item[0]),
    )

    total_weeks = max(len(week_range), 1)
    total_voyages = len(local_attended_times)

    return PocketWatchAnalysis(
        timezone_label=timezone_label,
        window_start=window_start,
        window_end=window_end,
        total_voyages=total_voyages,
        total_hosted=len(local_hosted_times),
        active_weeks=active_weeks,
        total_weeks=total_weeks,
        average_voyages_per_week=round(total_voyages / total_weeks, 2),
        average_voyages_per_active_week=round(total_voyages / active_weeks, 2),
        first_voyage_at=min(local_attended_times),
        last_voyage_at=max(local_attended_times),
        most_active_hour=most_active_hour,
        most_active_hour_count=most_active_hour_count,
        most_active_weekday=most_active_weekday,
        most_active_weekday_count=most_active_weekday_count,
        weekly_labels=tuple(week.strftime("%d %b") for week in week_range),
        weekly_attended_counts=weekly_attended_counts,
        weekly_hosted_counts=weekly_hosted_counts,
        weekday_counts=weekday_counts,
        hourly_counts=hourly_counts,
    )


def render_pocket_watch_chart(
        analysis: PocketWatchAnalysis,
        *,
        display_name: str,
        days: int,
) -> bytes:
    def plotter() -> None:
        figure = plt.figure(figsize=(15, 10))
        grid = figure.add_gridspec(2, 2, height_ratios=[1.35, 1])

        weekly_axis = figure.add_subplot(grid[0, :])
        weekday_axis = figure.add_subplot(grid[1, 0])
        hourly_axis = figure.add_subplot(grid[1, 1])

        weekly_positions = range(len(analysis.weekly_labels))
        weekly_axis.bar(
            weekly_positions,
            analysis.weekly_attended_counts,
            color="#1f77b4",
            label="Attended",
        )
        if analysis.hosted_activity_present:
            weekly_axis.plot(
                list(weekly_positions),
                analysis.weekly_hosted_counts,
                color="#ff7f0e",
                marker="o",
                linewidth=2,
                label="Hosted",
            )
        weekly_axis.set_title("Voyages per Week")
        weekly_axis.set_ylabel("Voyages")
        tick_positions = _build_weekly_tick_positions(len(analysis.weekly_labels))
        weekly_axis.set_xticks(tick_positions)
        weekly_axis.set_xticklabels(
            [analysis.weekly_labels[index] for index in tick_positions],
            rotation=45,
            ha="right",
        )
        weekly_axis.grid(axis="y", linestyle="--", alpha=0.25)
        weekly_axis.legend(loc="upper left")

        weekday_positions = range(len(WEEKDAY_LABELS))
        weekday_axis.bar(
            weekday_positions,
            analysis.weekday_counts,
            color="#2ca02c",
        )
        weekday_axis.set_title("Most Active Days")
        weekday_axis.set_ylabel("Voyages")
        weekday_axis.set_xticks(list(weekday_positions))
        weekday_axis.set_xticklabels(WEEKDAY_LABELS)
        weekday_axis.grid(axis="y", linestyle="--", alpha=0.25)

        hourly_positions = range(24)
        hourly_axis.bar(
            hourly_positions,
            analysis.hourly_counts,
            color="#9467bd",
        )
        hourly_axis.set_title("Most Active Hours")
        hourly_axis.set_ylabel("Voyages")
        hourly_axis.set_xticks(list(hourly_positions))
        hourly_axis.set_xticklabels([f"{hour:02d}" for hour in hourly_positions])
        hourly_axis.grid(axis="y", linestyle="--", alpha=0.25)

        if max(analysis.hourly_counts, default=0) > 0:
            hourly_axis.set_ylim(0, max(analysis.hourly_counts) + 1)
        if max(analysis.weekday_counts, default=0) > 0:
            weekday_axis.set_ylim(0, max(analysis.weekday_counts) + 1)

        figure.suptitle(
            (
                f"Pocket Watch for {display_name} | "
                f"Last {days} days | {analysis.timezone_label}"
            ),
            fontsize=16,
        )
        figure.text(
            0.5,
            0.94,
            (
                f"Attended: {analysis.total_voyages} | "
                f"Active weeks: {analysis.active_weeks}/{analysis.total_weeks} | "
                f"Peak hour: {analysis.most_active_hour_label} | "
                f"Peak day: {analysis.most_active_weekday_label}"
            ),
            ha="center",
            fontsize=10,
        )
        figure.tight_layout(rect=(0, 0, 1, 0.9))

    return render_matplotlib_plot_to_png(plotter)
