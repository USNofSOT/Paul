from __future__ import annotations

import io
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import discord
from matplotlib import pyplot as plt

from src.briefings.message import BriefingMessage
from src.config.briefings import (
    WEEKLY_BRIEFING_BUCKET_DAYS,
    WEEKLY_BRIEFING_POINT_COUNT,
)
from src.data.repository.ship_briefing_repository import ShipBriefingRepository
from src.utils.image_cache import render_matplotlib_plot_to_png

BACKGROUND = "#111a1f"
PANEL = "#1b262c"
GRID = "#34434a"
TEXT = "#edf2f4"
MUTED = "#93a4aa"
VOYAGE = "#4c8dff"
HOSTING = "#2bd673"
CREW = "#b06cff"
RED = "#ef3340"


@dataclass(frozen=True)
class WeeklyPoint:
    period_end: date
    voyage_count: int
    hosting_count: int
    crew_size: int


@dataclass(frozen=True)
class WeeklyShipBriefing:
    ship_role_id: int
    ship_name: str
    points: tuple[WeeklyPoint, ...]


def build_weekly_briefing(
    repository: ShipBriefingRepository,
    *,
    ship_role_id: int,
    ship_name: str,
    current_ship_size: int,
    reference_time: datetime,
) -> WeeklyShipBriefing:
    points: list[WeeklyPoint] = []
    for offset in reversed(range(WEEKLY_BRIEFING_POINT_COUNT)):
        end = reference_time - timedelta(days=offset * WEEKLY_BRIEFING_BUCKET_DAYS)
        start = end - timedelta(days=WEEKLY_BRIEFING_BUCKET_DAYS)
        if offset == 0:
            crew_size = current_ship_size
        else:
            historical_size = repository.get_ship_size_on_or_before(
                ship_role_id=ship_role_id,
                before=end,
            )
            crew_size = historical_size if historical_size is not None else 0
        points.append(
            WeeklyPoint(
                period_end=end.date(),
                voyage_count=repository.count_voyage_logs_between(
                    ship_role_id=ship_role_id,
                    start=start,
                    end=end,
                ),
                hosting_count=repository.count_hosting_logs_between(
                    ship_role_id=ship_role_id,
                    start=start,
                    end=end,
                ),
                crew_size=crew_size,
            )
        )
    return WeeklyShipBriefing(
        ship_role_id=ship_role_id,
        ship_name=ship_name,
        points=tuple(points),
    )


def compose_weekly_briefing_messages(
    briefing: WeeklyShipBriefing,
    *,
    concerns: Mapping[str, bool],
) -> tuple[BriefingMessage, ...]:
    messages: list[BriefingMessage] = []
    if concerns.get("activity", False):
        filename = f"weekly_activity_{briefing.ship_role_id}.png"
        image = render_activity_image(briefing)
        embed = discord.Embed(color=discord.Color.blue())
        embed.set_image(url=f"attachment://{filename}")
        messages.append(
            BriefingMessage(
                embeds=(embed,),
                files=(discord.File(io.BytesIO(image), filename=filename),),
            )
        )
    if concerns.get("crew", False):
        filename = f"weekly_crew_{briefing.ship_role_id}.png"
        image = render_crew_image(briefing)
        embed = discord.Embed(color=discord.Color.purple())
        embed.set_image(url=f"attachment://{filename}")
        messages.append(
            BriefingMessage(
                embeds=(embed,),
                files=(discord.File(io.BytesIO(image), filename=filename),),
            )
        )
    return tuple(messages)


def render_activity_image(briefing: WeeklyShipBriefing) -> bytes:
    labels = [point.period_end.strftime("%d %b") for point in briefing.points]
    voyages = [point.voyage_count for point in briefing.points]
    hosted = [point.hosting_count for point in briefing.points]

    def plotter() -> None:
        figure = plt.figure(
            figsize=(8, 5.2),
            dpi=150,
            facecolor=BACKGROUND,
        )
        _draw_header(
            figure,
            ship_name=briefing.ship_name,
            section="ACTIVITY",
            context="4 × 7-day UTC windows",
        )
        voyage_axes = figure.add_axes((0.07, 0.54, 0.86, 0.23))
        _draw_trend(
            voyage_axes,
            values=voyages,
            labels=labels,
            label="Voyage participations",
            color=VOYAGE,
            start_at_zero=True,
        )
        hosting_axes = figure.add_axes((0.07, 0.13, 0.86, 0.23))
        _draw_trend(
            hosting_axes,
            values=hosted,
            labels=labels,
            label="Hosted voyages",
            color=HOSTING,
            start_at_zero=True,
        )

    return render_matplotlib_plot_to_png(plotter)


def render_crew_image(briefing: WeeklyShipBriefing) -> bytes:
    labels = [point.period_end.strftime("%d %b") for point in briefing.points]
    crew = [point.crew_size for point in briefing.points]

    def plotter() -> None:
        figure = plt.figure(
            figsize=(8, 3.3),
            dpi=150,
            facecolor=BACKGROUND,
        )
        _draw_header(
            figure,
            ship_name=briefing.ship_name,
            section="CREW",
            context="4 weekly UTC snapshots",
        )
        axes = figure.add_axes((0.07, 0.18, 0.86, 0.54))
        _draw_trend(
            axes,
            values=crew,
            labels=labels,
            label="Crew size",
            color=CREW,
            start_at_zero=False,
        )

    return render_matplotlib_plot_to_png(plotter)


def _draw_trend(
    axes,
    *,
    values: Sequence[int],
    labels: Sequence[str],
    label: str,
    color: str,
    start_at_zero: bool,
) -> None:
    positions = list(range(len(values)))
    axes.set_facecolor(PANEL)
    current = values[-1]
    previous = values[-2]
    delta = current - previous

    lowest = min(values)
    highest = max(values)
    if start_at_zero:
        lower = 0
        upper = max(1, highest * 1.25)
    else:
        padding = max(2, (highest - lowest) * 0.75)
        lower = max(0, lowest - padding)
        upper = highest + padding
    axes.set_ylim(lower, upper)

    axes.plot(
        positions,
        values,
        color=color,
        linewidth=2.5,
        marker="o",
        markersize=6,
        zorder=3,
    )
    axes.fill_between(
        positions,
        values,
        lower,
        color=color,
        alpha=0.10,
        zorder=2,
    )
    grid_lines = [lower + (upper - lower) * ratio for ratio in (0.25, 0.5, 0.75)]
    axes.set_yticks(grid_lines)
    axes.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.55)
    axes.tick_params(axis="y", left=False, labelleft=False)
    axes.set_xticks(positions, labels)
    axes.tick_params(
        axis="x",
        colors=MUTED,
        labelsize=8,
        length=0,
        pad=8,
    )
    for spine in axes.spines.values():
        spine.set_visible(False)
    axes.set_axisbelow(True)
    axes.margins(x=0.08)

    axes.text(
        0,
        1.18,
        label,
        transform=axes.transAxes,
        color=TEXT,
        fontsize=11,
        fontweight="bold",
        ha="left",
        va="center",
    )
    axes.text(
        0.74,
        1.18,
        f"{current} current",
        transform=axes.transAxes,
        color=TEXT,
        fontsize=9,
        fontweight="bold",
        ha="right",
        va="center",
    )
    axes.text(
        1,
        1.18,
        _format_delta(current, previous),
        transform=axes.transAxes,
        color=MUTED if delta == 0 else HOSTING if delta > 0 else RED,
        fontsize=8.5,
        fontweight="bold",
        ha="right",
        va="center",
    )
    for position, value in zip(positions, values, strict=True):
        axes.annotate(
            str(value),
            (position, value),
            xytext=(0, 9),
            textcoords="offset points",
            color=TEXT,
            fontsize=8.5,
            fontweight="bold",
            ha="center",
            zorder=4,
        )


def _draw_header(
    figure,
    *,
    ship_name: str,
    section: str,
    context: str,
) -> None:
    figure.text(
        0.07,
        0.965,
        ship_name,
        color=TEXT,
        fontsize=17,
        fontweight="bold",
        ha="left",
        va="top",
    )
    figure.text(
        0.07,
        0.885,
        f"WEEKLY BRIEFING · {section} · {context}",
        color=MUTED,
        fontsize=9,
        fontweight="bold",
        ha="left",
        va="top",
    )


def _format_delta(current: int, previous: int) -> str:
    delta = current - previous
    if delta == 0:
        return "No change"
    arrow = "↑" if delta > 0 else "↓"
    return f"{arrow} {abs(delta)} WoW"
