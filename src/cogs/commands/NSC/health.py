from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime

import discord
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import psutil
from discord import app_commands
from discord.ext import commands

from src.config import IMAGE_CACHES, NSC_ROLES
from src.data import HealthSnapshot
from src.data.engine import engine
from src.data.repository.health_snapshot_repository import HealthSnapshotRepository
from src.data.repository.system_repository import SystemRepository
from src.utils.embeds import default_embed
from src.utils.image_cache import BinaryImageCache, render_matplotlib_plot_to_png
from src.utils.ip_utils import mask_ip

log = logging.getLogger(__name__)

_PROCESS = psutil.Process()
_PERF_WINDOWS = [1, 3, 6, 12, 24]

# Color Palette
C_GREEN = "#2ecc71"
C_RED = "#e74c3c"
C_BLUE = "#3498db"
C_PURPLE = "#9b59b6"
C_ORANGE = "#f39c12"
C_DARK = "#2c3e50"

HEALTH_LATENCY_CACHE = BinaryImageCache(IMAGE_CACHES["health_latency_chart"])
HEALTH_CONNECTIONS_CACHE = BinaryImageCache(IMAGE_CACHES["health_connections_chart"])
HEALTH_POOL_CACHE = BinaryImageCache(IMAGE_CACHES["health_pool_chart"])
HEALTH_MEMORY_CACHE = BinaryImageCache(IMAGE_CACHES["health_memory_chart"])


def _apply_chart_styling(ax, title: str, ylabel: str, snapshots: list | None = None):
    """Apply consistent USN-style aesthetics to all charts."""
    plt.style.use("bmh")
    ax.set_title(title, fontsize=15, pad=20, fontweight="bold", color=C_DARK)
    ax.set_ylabel(ylabel, fontsize=11, fontweight="semibold")
    ax.grid(True, linestyle=":", alpha=0.6, zorder=1)

    if snapshots:
        ax.set_xlabel("Time (UTC)", fontsize=11, fontweight="semibold")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))
        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=9)
    else:
        ax.set_xlabel("Metrics", fontsize=11, fontweight="semibold")


def _build_latency_chart(snapshots: list[HealthSnapshot]) -> bytes:
    def plotter():
        fig, ax = plt.subplots(figsize=(10, 6))
        if not snapshots:
            ax.text(0.5, 0.5, "No snapshot data available", ha="center", va="center")
            _apply_chart_styling(ax, "Command Latency Trends", "Execution Latency (ms)")
            return

        times = [s.timestamp for s in snapshots]
        avg = [s.avg_cmd_latency or 0 for s in snapshots]
        max_ = [s.max_cmd_latency or 0 for s in snapshots]

        # Requirement: Solid green line with semi-transparent green area fill
        ax.plot(times, avg, label="Average Latency", color=C_GREEN, linewidth=2.5, zorder=3)
        ax.fill_between(times, avg, color=C_GREEN, alpha=0.3, zorder=2)

        # Requirement: Red dashed line hovering above the average
        ax.plot(
            times,
            max_,
            label="Maximum Latency",
            color=C_RED,
            alpha=0.7,
            linestyle="--",
            linewidth=1.5,
            zorder=4,
        )

        _apply_chart_styling(
            ax, "Bot Command Latency (Last 24h)", "Execution Latency (ms)", snapshots
        )
        ax.set_xlabel("Time (24-hour intervals)", fontsize=11, fontweight="semibold")
        ax.legend(loc="upper right", frameon=True, facecolor="white", shadow=True)
        plt.tight_layout()

    return render_matplotlib_plot_to_png(plotter)


def _build_connections_chart(rows: list[dict]) -> bytes:
    ip_counts: dict[str, int] = {}
    for row in rows:
        host_raw = row.get("Host") or ""
        host = host_raw.rsplit(":", 1)[0] if host_raw else "unknown"
        masked = mask_ip(host) if host else "unknown"
        ip_counts[masked] = ip_counts.get(masked, 0) + 1

    def plotter():
        fig, ax = plt.subplots(figsize=(10, 6))
        if not ip_counts:
            ax.text(0.5, 0.5, "No active connections", ha="center", va="center")
            _apply_chart_styling(ax, "Active Connections by IP", "Masked IP")
            return

        # Requirement: Sort Descending (most connections at the top)
        # barh renders bottom-to-top, so we sort ASCENDING to get DESCENDING visually
        sorted_items = sorted(ip_counts.items(), key=lambda item: item[1])
        ips = [item[0] for item in sorted_items]
        counts = [item[1] for item in sorted_items]

        bars = ax.barh(
            ips, counts, color=C_BLUE, edgecolor="white", alpha=0.85, zorder=3
        )

        # Requirement: Exact number value prominently at the far right end
        for bar in bars:
            width = bar.get_width()
            ax.text(
                width + 0.15,
                bar.get_y() + bar.get_height() / 2,
                f"{int(width)}",
                va="center",
                fontweight="bold",
                color=C_DARK,
                fontsize=12,
            )

        _apply_chart_styling(ax, "Active DB Connections by Source", "Masked IP")
        ax.set_xlabel("Process Count", fontsize=11, fontweight="semibold")

        # Scaling room for data labels
        if counts:
            ax.set_xlim(0, max(counts) * 1.25)

        plt.tight_layout()

    return render_matplotlib_plot_to_png(plotter)


def _build_pool_chart(snapshots: list[HealthSnapshot], size_limit: int) -> bytes:
    def plotter():
        fig, ax = plt.subplots(figsize=(10, 6))
        if not snapshots:
            ax.text(0.5, 0.5, "No pool history available", ha="center", va="center")
            _apply_chart_styling(ax, "Connection Pool Utilization", "Connections")
            return

        times = [s.timestamp for s in snapshots]
        # Requirement: Stacked Layers: Bottom 'Checked Out', stacked directly on top 'Idle'
        busy = [max(0, s.checked_out) for s in snapshots]
        idle = [max(0, s.checked_in) for s in snapshots]
        burst = [max(0, s.overflow) for s in snapshots]

        ax.stackplot(
            times,
            busy,
            idle,
            burst,
            labels=["Checked Out (Busy)", "Idle (In Pool)", "Overflow (Burst)"],
            colors=[C_RED, C_GREEN, C_ORANGE],
            alpha=0.8,
            zorder=2,
        )

        # Requirement: Prominent dashed horizontal line at Y limit
        ax.axhline(
            y=size_limit,
            color=C_DARK,
            linestyle="--",
            linewidth=2.5,
            label="Size Limit",
            zorder=5,
        )

        # Requirement: Strict Y-Axis starting at 0
        ax.set_ylim(bottom=0)

        _apply_chart_styling(
            ax, "DB Connection Pool (Last 24h)", "Connections", snapshots
        )
        ax.set_xlabel("Time (24-hour intervals)", fontsize=11, fontweight="semibold")
        ax.legend(loc="upper left", frameon=True, facecolor="white", shadow=True)
        plt.tight_layout()

    return render_matplotlib_plot_to_png(plotter)


def _build_memory_chart(
        snapshots: list[HealthSnapshot], current_mb: float
) -> bytes:
    def plotter():
        fig, ax = plt.subplots(figsize=(10, 6))
        if not snapshots:
            ax.text(0.5, 0.5, "No memory history available", ha="center", va="center")
            _apply_chart_styling(ax, "Bot Memory Usage", "Memory (MB)")
            return

        times = [s.timestamp for s in snapshots]
        m_mb = [s.memory_usage_mb for s in snapshots]

        # Requirement: Single purple line with distinct circular markers
        ax.plot(
            times,
            m_mb,
            color=C_PURPLE,
            linewidth=3,
            marker="o",
            markersize=6,
            markevery=max(1, len(snapshots) // 24),
            zorder=3,
            label="Memory Usage",
        )
        ax.fill_between(times, m_mb, color=C_PURPLE, alpha=0.15, zorder=2)

        # Requirement: Status tag at the final data point (Memory Only)
        if times:
            ax.annotate(
                f"{current_mb:.1f} MB",
                xy=(times[-1], m_mb[-1]),
                xytext=(15, 0),
                textcoords="offset points",
                va="center",
                bbox=dict(
                    boxstyle="round,pad=0.5", fc="white", ec=C_PURPLE, alpha=0.9, lw=2
                ),
                arrowprops=dict(arrowstyle="->", color=C_PURPLE, lw=1.5),
                fontsize=10,
                fontweight="bold",
            )

        _apply_chart_styling(
            ax, "Bot Memory Consumption (Last 24h)", "Memory (MB)", snapshots
        )
        ax.set_xlabel("Time (24-hour intervals)", fontsize=11, fontweight="semibold")

        # Requirement: Bounded closely to data (not starting at 0)
        if m_mb:
            r = max(m_mb) - min(m_mb)
            padding = max(r * 0.4, 5.0)
            ax.set_ylim(min(m_mb) - padding, max(m_mb) + padding)

        plt.tight_layout()

    return render_matplotlib_plot_to_png(plotter)


def _build_performance_embed(snapshot: HealthSnapshot | None) -> discord.Embed:
    embed = default_embed(
        title="📊 Performance Trends",
        description="Average and max command latency over recent windows.",
    )
    if snapshot is None:
        embed.add_field(
            name="No data", value="No health snapshots recorded yet.", inline=False
        )
        return embed

    repo = HealthSnapshotRepository()
    try:
        for hours in _PERF_WINDOWS:
            avg_ms, max_ms = repo.get_avg_max_latency(hours)
            avg = f"{avg_ms:.1f} ms" if avg_ms is not None else "—"
            max_ = f"{max_ms:.1f} ms" if max_ms is not None else "—"
            embed.add_field(
                name=f"Last {hours}h", value=f"avg: {avg}\nmax: {max_}", inline=True
            )
    finally:
        repo.close_session()
    return embed


def _build_connections_embed() -> discord.Embed:
    embed = default_embed(
        title="🔌 Active Connections",
        description="Current processes from `SHOW PROCESSLIST`.",
    )
    repo = SystemRepository()
    try:
        rows = repo.get_process_list()
    finally:
        repo.close_session()

    ip_counts: dict[str, int] = {}
    for row in rows:
        host_raw = row.get("Host") or ""
        host = host_raw.rsplit(":", 1)[0] if host_raw else ""
        masked = mask_ip(host) if host else "unknown"
        ip_counts[masked] = ip_counts.get(masked, 0) + 1

    if not ip_counts:
        embed.add_field(
            name="No connections", value="Process list is empty.", inline=False
        )
        return embed

    lines = [f"`{ip}` — {count} process(es)" for ip, count in sorted(ip_counts.items())]
    embed.add_field(
        name=f"Total processes: {len(rows)}", value="\n".join(lines), inline=False
    )
    return embed


def _build_pool_embed() -> discord.Embed:
    pool = engine.pool
    embed = default_embed(
        title="🚰 Database Pool",
        description="Current SQLAlchemy connection pool status.",
    )

    # Some pool types or configurations can return negative values for overflow
    # if the pool is not full. We clamp it to 0 for display.
    checked_out = max(0, pool.checkedout())
    idle = max(0, pool.checkedin())
    overflow = max(0, pool.overflow())
    size = pool.size()

    embed.add_field(name="Pool Type", value=type(pool).__name__, inline=False)
    embed.add_field(name="📤 Checked Out", value=str(checked_out), inline=True)
    embed.add_field(name="😴 In Pool (Idle)", value=str(idle), inline=True)
    embed.add_field(name="🏗️ Size Limit", value=str(size), inline=True)
    embed.add_field(name="🌊 Overflow", value=str(overflow), inline=True)
    embed.add_field(
        name="📊 Total Active", value=str(checked_out + idle + overflow), inline=True
    )

    return embed


def _build_system_embed(
        snapshot: HealthSnapshot | None, bot_start_time: datetime | None = None
) -> discord.Embed:
    memory_mb = _PROCESS.memory_info().rss / (1024 * 1024)
    reference = bot_start_time or datetime.now(tz=UTC)
    uptime = datetime.now(tz=UTC) - reference
    h, rem = divmod(int(uptime.total_seconds()), 3600)
    m, s = divmod(rem, 60)

    embed = default_embed(
        title="🖥️ System Resources", description="Live process and memory stats."
    )
    embed.add_field(name="Memory (RSS)", value=f"{memory_mb:.1f} MB", inline=True)
    embed.add_field(name="Uptime", value=f"{h}h {m}m {s}s", inline=True)

    if snapshot:
        now = datetime.now(tz=UTC).replace(tzinfo=None)
        age_s = int((now - snapshot.timestamp).total_seconds())
        embed.add_field(
            name="Snapshot Memory", value=f"{snapshot.memory_usage_mb} MB", inline=True
        )
        embed.add_field(name="Last Snapshot", value=f"{age_s}s ago", inline=True)

    return embed


_VIEW_CHOICES = [
    discord.SelectOption(label="📊 Performance Trends", value="performance"),
    discord.SelectOption(label="🔌 Active Connections", value="connections"),
    discord.SelectOption(label="🚰 Database Pool", value="pool"),
    discord.SelectOption(label="🖥️ System Resources", value="system"),
]


class _HealthSelect(discord.ui.Select):
    def __init__(self, bot_start_time: datetime | None):
        self._bot_start_time = bot_start_time
        super().__init__(placeholder="Select a view…", options=_VIEW_CHOICES)

    async def callback(self, interaction: discord.Interaction):
        self.view.current_choice = self.values[0]
        await self.view.refresh(interaction)


class _HealthView(discord.ui.View):
    def __init__(self, bot_start_time: datetime | None):
        super().__init__(timeout=300)
        self._bot_start_time = bot_start_time
        self.current_choice = "performance"
        self.add_item(_HealthSelect(bot_start_time))

    async def refresh(self, interaction: discord.Interaction):
        choice = self.current_choice
        repo = HealthSnapshotRepository()

        try:
            # Calculate precision uptime
            reference = self._bot_start_time or datetime.now(tz=UTC)
            uptime_delta = datetime.now(tz=UTC) - reference
            total_s = int(uptime_delta.total_seconds())
            h, rem = divmod(total_s, 3600)
            m, _ = divmod(rem, 60)
            uptime_str = f"{h}H {m}M"

            if choice == "performance":
                snapshot = repo.get_latest()
                history = repo.get_recent_snapshots(24)
                embed = await asyncio.to_thread(_build_performance_embed, snapshot)

                chart_data = await asyncio.to_thread(
                    HEALTH_LATENCY_CACHE.get_or_create_bytes,
                    {"history_ids": [s.id for s in history]},
                    lambda: _build_latency_chart(history),
                )
                file = HEALTH_LATENCY_CACHE.to_discord_file(chart_data)

            elif choice == "connections":
                system_repo = SystemRepository()
                try:
                    rows = system_repo.get_process_list()
                finally:
                    system_repo.close_session()

                embed = await asyncio.to_thread(_build_connections_embed)
                chart_data = await asyncio.to_thread(
                    HEALTH_CONNECTIONS_CACHE.get_or_create_bytes,
                    {"rows": rows},
                    lambda: _build_connections_chart(rows),
                )
                file = HEALTH_CONNECTIONS_CACHE.to_discord_file(chart_data)

            elif choice == "pool":
                history = repo.get_recent_snapshots(24)
                embed = _build_pool_embed()
                # Pass size_limit from engine config
                from src.data.engine import engine

                size_limit = engine.pool.size()

                chart_data = await asyncio.to_thread(
                    HEALTH_POOL_CACHE.get_or_create_bytes,
                    {"history_ids": [s.id for s in history], "limit": size_limit},
                    lambda: _build_pool_chart(history, size_limit),
                )
                file = HEALTH_POOL_CACHE.to_discord_file(chart_data)

            else:  # system
                snapshot = repo.get_latest()
                history = repo.get_recent_snapshots(24)
                embed = await asyncio.to_thread(
                    _build_system_embed, snapshot, self._bot_start_time
                )

                current_memory = _PROCESS.memory_info().rss / (1024 * 1024)

                chart_data = await asyncio.to_thread(
                    HEALTH_MEMORY_CACHE.get_or_create_bytes,
                    {
                        "history_ids": [s.id for s in history],
                        "curr": current_memory,
                        "uptime": uptime_str,
                    },
                    lambda: _build_memory_chart(history, current_memory),
                )
                file = HEALTH_MEMORY_CACHE.to_discord_file(chart_data)

        finally:
            repo.close_session()

        embed.set_image(url=f"attachment://{file.filename}")

        if interaction.response.is_done():
            await interaction.edit_original_response(
                embed=embed, attachments=[file], view=self
            )
        else:
            await interaction.response.edit_message(
                embed=embed, attachments=[file], view=self
            )

    @discord.ui.button(label="🔄 Reload", style=discord.ButtonStyle.gray)
    async def reload(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.refresh(interaction)


class Health(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="health",
        description="View bot health, performance trends, and database status.",
    )
    @app_commands.checks.has_any_role(*NSC_ROLES)
    async def health(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        # bot.start_time is set by our Bot class in core/bot.py
        bot_start_time = getattr(self.bot, "start_time", None)
        view = _HealthView(bot_start_time)
        await view.refresh(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Health(bot))
