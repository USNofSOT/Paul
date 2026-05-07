import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict

import discord
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt
import numpy as np

from src.config import IMAGE_CACHES
from src.config.ping_tracking import PING_TRACKING_CONFIG
from src.config.ranks import RANKS
from src.data.repository.ping_tracking_repository import PingTrackingRepository
from src.security import require_any_role, Role
from src.utils.embeds import error_embed
from src.utils.image_cache import BinaryImageCache, render_matplotlib_plot_to_png
from src.utils.time_utils import utc_time_now

log = logging.getLogger(__name__)

PING_USAGE_TREND_CACHE = BinaryImageCache(IMAGE_CACHES["ping_usage_trend"])

WEEKDAY_LABELS = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")

UNIQUE_PING_ROLE_IDS = list(set(
    role_id
    for channel_config in PING_TRACKING_CONFIG.values()
    for role_id in channel_config.keys()
))

# Granularity options: value -> (label, description)
GRANULARITY_OPTIONS = {
    "hour":  ("Per Hour",  "Break data into individual hours"),
    "day":   ("Per Day",   "Break data into individual days"),
    "week":  ("Per Week",  "Break data into calendar weeks"),
    "month": ("Per Month", "Break data into calendar months"),
}

# Default period spans for each granularity (number of buckets shown)
GRANULARITY_DEFAULTS = {
    "hour":  48,   # last 48 hours
    "day":   30,   # last 30 days
    "week":  12,   # last 12 weeks
    "month": 12,   # last 12 months
}

# Max buckets allowed per granularity
GRANULARITY_MAX = {
    "hour":  168,  # 1 week of hours
    "day":   90,
    "week":  52,
    "month": 24,
}


def _now_floor() -> datetime:
    """Return current UTC time floored to the current hour."""
    return utc_time_now().replace(tzinfo=None).replace(minute=0, second=0, microsecond=0)


def _bucket_for(dt: datetime, granularity: str) -> datetime:
    """Return the start of the bucket that `dt` falls into."""
    if granularity == "hour":
        return dt.replace(minute=0, second=0, microsecond=0)
    if granularity == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if granularity == "week":
        base = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return base - timedelta(days=base.weekday())
    if granularity == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unknown granularity: {granularity}")


def _generate_buckets(granularity: str, n: int) -> list[datetime]:
    """Generate n bucket-start datetimes ending at the current bucket."""
    now = _now_floor()
    current = _bucket_for(now, granularity)
    buckets = []
    for i in range(n - 1, -1, -1):
        if granularity == "hour":
            buckets.append(current - timedelta(hours=i))
        elif granularity == "day":
            buckets.append(current - timedelta(days=i))
        elif granularity == "week":
            buckets.append(current - relativedelta(weeks=i))
        elif granularity == "month":
            buckets.append(current - relativedelta(months=i))
    return buckets


def _bucket_label(dt: datetime, granularity: str) -> str:
    if granularity == "hour":
        return dt.strftime("%d %b %H:%M")
    if granularity == "day":
        return dt.strftime("%d %b")
    if granularity == "week":
        return dt.strftime("%d %b")
    if granularity == "month":
        return dt.strftime("%b %Y")
    return str(dt)


def _start_date_for(buckets: list[datetime], granularity: str) -> datetime:
    """Return the earliest datetime we need to fetch."""
    return buckets[0]


class PingUsageFilterSelect(discord.ui.Select):
    def __init__(self, current_filter: str, guild: discord.Guild):
        options = [
            discord.SelectOption(
                label="All Voyage LFG",
                description="Aggregated view of all Voyage pings.",
                value="ALL",
                default=current_filter == "ALL"
            )
        ]

        for role_id in UNIQUE_PING_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                options.append(
                    discord.SelectOption(
                        label=role.name,
                        description=f"View activity for {role.name} pings.",
                        value=str(role_id),
                        default=current_filter == str(role_id)
                    )
                )
        super().__init__(placeholder="Select ping category...", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: PingUsageView = self.view
        view.filter_group = self.values[0]
        embed, discord_file = await view.cog.trend_ping_usage(
            interaction, view.n_buckets, view.filter_group, view.granularity
        )
        view.update_select()
        await interaction.edit_original_response(embed=embed, attachments=[discord_file], view=view)


class PingUsageGranularitySelect(discord.ui.Select):
    def __init__(self, current_granularity: str):
        options = [
            discord.SelectOption(
                label=GRANULARITY_OPTIONS[g][0],
                description=GRANULARITY_OPTIONS[g][1],
                value=g,
                default=current_granularity == g,
            )
            for g in GRANULARITY_OPTIONS
        ]
        super().__init__(placeholder="Select time granularity...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: PingUsageView = self.view
        new_gran = self.values[0]
        if new_gran != view.granularity:
            view.granularity = new_gran
            # Reset bucket count to the sensible default for this granularity
            view.n_buckets = GRANULARITY_DEFAULTS[new_gran]
        embed, discord_file = await view.cog.trend_ping_usage(
            interaction, view.n_buckets, view.filter_group, view.granularity
        )
        view.update_select()
        await interaction.edit_original_response(embed=embed, attachments=[discord_file], view=view)


class PingUsageView(discord.ui.View):
    def __init__(self, cog: 'PingUsage', filter_group: str, n_buckets: int,
                 granularity: str, guild: discord.Guild):
        super().__init__(timeout=180)
        self.cog = cog
        self.filter_group = filter_group
        self.n_buckets = n_buckets
        self.granularity = granularity
        self.guild = guild
        self.update_select()

    def update_select(self):
        self.clear_items()
        self.add_item(PingUsageFilterSelect(self.filter_group, self.guild))
        self.add_item(PingUsageGranularitySelect(self.granularity))


class PingUsage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping_usage", description="Get a report of LFG ping usage and deficiencies over time")
    @app_commands.describe(periods="Number of time periods to show (default varies by granularity)")
    @app_commands.describe(granularity="Time granularity: hour, day, week (default), month")
    @app_commands.describe(hidden="Should only you be able to see the response?")
    @app_commands.choices(granularity=[
        app_commands.Choice(name="Per Hour", value="hour"),
        app_commands.Choice(name="Per Day", value="day"),
        app_commands.Choice(name="Per Week", value="week"),
        app_commands.Choice(name="Per Month", value="month"),
    ])
    @require_any_role(Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR)
    async def ping_usage(self, interaction: discord.Interaction,
                         granularity: str = "week",
                         periods: int = 0,
                         hidden: bool = True):
        try:
            await interaction.response.defer(ephemeral=hidden)

            n_buckets = periods if periods > 0 else GRANULARITY_DEFAULTS[granularity]
            max_buckets = GRANULARITY_MAX[granularity]
            if n_buckets > max_buckets:
                await interaction.followup.send(
                    embed=error_embed(f"Cannot show more than {max_buckets} periods for '{granularity}' granularity."),
                    ephemeral=True
                )
                return

            embed, discord_file = await self.trend_ping_usage(
                interaction, n_buckets, filter_group="ALL", granularity=granularity
            )
            view = PingUsageView(
                self, filter_group="ALL", n_buckets=n_buckets,
                granularity=granularity, guild=interaction.guild
            )
            await interaction.followup.send(embed=embed, file=discord_file, view=view)

        except Exception as e:
            log.error(f"Error getting ping usage trend: {e}", exc_info=True)
            await interaction.followup.send(embed=error_embed("Error generating the ping usage report."), ephemeral=True)

    async def trend_ping_usage(self, interaction: discord.Interaction,
                               n_buckets: int, filter_group: str, granularity: str):
        buckets = _generate_buckets(granularity, n_buckets)
        start_date = _start_date_for(buckets, granularity)

        with PingTrackingRepository() as ping_repo:
            all_logs = ping_repo.get_active_ping_logs_since(start_date)

        if filter_group == "ALL":
            logs = all_logs
            filter_name = "All Voyage LFG"
        else:
            role_id = int(filter_group)
            logs = [e for e in all_logs if e.ping_role_id == role_id]
            role = interaction.guild.get_role(role_id)
            filter_name = role.name if role else f"Role {role_id}"

        total_pings = len(logs)
        vp_enabled_pings = sum(1 for e in logs if e.has_vp_permission)
        non_vp_pings = total_pings - vp_enabled_pings

        # --- Bucketed trend ---
        bucket_total: dict[datetime, int] = defaultdict(int)
        bucket_vp: dict[datetime, int] = defaultdict(int)
        bucket_non_vp: dict[datetime, int] = defaultdict(int)

        # --- Day-of-week and hourly distributions (VP/non-VP) ---
        weekday_vp_counts = {i: 0 for i in range(7)}
        weekday_non_vp_counts = {i: 0 for i in range(7)}
        hourly_vp_counts = {i: 0 for i in range(24)}
        hourly_non_vp_counts = {i: 0 for i in range(24)}

        # --- Rank distribution ---
        rank_lookup: dict[int, str] = {}
        for rank in RANKS:
            for rid in rank.role_ids:
                rank_lookup[rid] = rank.name

        rank_vp_counts: dict[str, int] = defaultdict(int)
        rank_non_vp_counts: dict[str, int] = defaultdict(int)

        for entry in logs:
            b = _bucket_for(entry.created_at, granularity)
            bucket_total[b] += 1
            if entry.has_vp_permission:
                bucket_vp[b] += 1
            else:
                bucket_non_vp[b] += 1

            wd = entry.created_at.weekday()
            hr = entry.created_at.hour
            if entry.has_vp_permission:
                weekday_vp_counts[wd] += 1
                hourly_vp_counts[hr] += 1
            else:
                weekday_non_vp_counts[wd] += 1
                hourly_non_vp_counts[hr] += 1

            rank_name = rank_lookup.get(entry.highest_rank_role_id, "Unknown Rank")
            if entry.has_vp_permission:
                rank_vp_counts[rank_name] += 1
            else:
                rank_non_vp_counts[rank_name] += 1

        # Build ordered series for trend chart
        y_total = [bucket_total.get(b, 0) for b in buckets]
        y_vp = [bucket_vp.get(b, 0) for b in buckets]
        y_non_vp = [bucket_non_vp.get(b, 0) for b in buckets]

        # Rank chart
        unique_ranks = list(set(list(rank_vp_counts.keys()) + list(rank_non_vp_counts.keys())))
        unique_ranks.sort(key=lambda r: rank_vp_counts.get(r, 0) + rank_non_vp_counts.get(r, 0), reverse=True)
        y_rank_vp = [rank_vp_counts.get(r, 0) for r in unique_ranks]
        y_rank_non_vp = [rank_non_vp_counts.get(r, 0) for r in unique_ranks]

        # Stats
        active_buckets = sum(1 for v in y_total if v > 0)
        avg_per_bucket = round(total_pings / max(n_buckets, 1), 2)
        gran_label = GRANULARITY_OPTIONS[granularity][0]

        weekday_total = {i: weekday_vp_counts[i] + weekday_non_vp_counts[i] for i in range(7)}
        hourly_total = {i: hourly_vp_counts[i] + hourly_non_vp_counts[i] for i in range(24)}
        most_active_hour = max(hourly_total.keys(), key=lambda k: hourly_total[k]) if total_pings > 0 else 0
        most_active_weekday = max(weekday_total.keys(), key=lambda k: weekday_total[k]) if total_pings > 0 else 0
        most_active_hour_label = f"{most_active_hour:02d}:00-{(most_active_hour + 1) % 24:02d}:00"
        most_active_weekday_label = WEEKDAY_LABELS[most_active_weekday]

        # Determine x-tick label density (avoid crowding)
        n = len(buckets)
        tick_step = max(1, n // 20)

        def plotter():
            figure = plt.figure(figsize=(16, 15))
            grid = figure.add_gridspec(3, 2, height_ratios=[1.35, 1.35, 1])

            trend_axis = figure.add_subplot(grid[0, :])
            rank_axis = figure.add_subplot(grid[1, :])
            weekday_axis = figure.add_subplot(grid[2, 0])
            hourly_axis = figure.add_subplot(grid[2, 1])

            positions = range(n)
            labels = [_bucket_label(b, granularity) for b in buckets]
            sparse_labels = [labels[i] if i % tick_step == 0 else "" for i in range(n)]

            # --- Trend chart ---
            trend_axis.bar(positions, y_total, color="#8CB9D1", label="Total Pings", alpha=0.4)
            if total_pings > 0:
                trend_axis.plot(list(positions), y_vp, color="#2ECC71", marker="o",
                                linewidth=2.5, markersize=6, label="VP Enabled")
                trend_axis.plot(list(positions), y_non_vp, color="#E74C3C", marker="o",
                                linewidth=2.5, markersize=6, label="Non-VP (Deficient)")
            trend_axis.set_title(f"Ping Volume {gran_label}: {filter_name}")
            trend_axis.set_xlabel("Period")
            trend_axis.set_ylabel("Pings")
            trend_axis.set_xticks(list(positions))
            trend_axis.set_xticklabels(sparse_labels, rotation=45, ha="right", fontsize=8)
            trend_axis.grid(axis="y", linestyle="--", alpha=0.25)
            trend_axis.legend(loc="upper left")

            # --- Rank distribution stacked bar ---
            if unique_ranks:
                rank_positions = np.arange(len(unique_ranks))
                rank_axis.bar(rank_positions, y_rank_vp, color="#2ECC71", label="VP Enabled", alpha=0.85)
                rank_axis.bar(rank_positions, y_rank_non_vp, bottom=y_rank_vp,
                              color="#E74C3C", label="Non-VP (Deficient)", alpha=0.85)
                rank_axis.set_title(f"Rank Distribution: {filter_name}")
                rank_axis.set_ylabel("Pings")
                rank_axis.set_xticks(rank_positions)
                rank_axis.set_xticklabels(unique_ranks, rotation=45, ha="right", fontsize=8)
                rank_axis.grid(axis="y", linestyle="--", alpha=0.25)
                rank_axis.legend(loc="upper right")
            else:
                rank_axis.set_title(f"Rank Distribution: {filter_name}")
                rank_axis.text(0.5, 0.5, "No rank data available", ha="center", va="center",
                               transform=rank_axis.transAxes)

            # --- Weekday VP/Non-VP stacked bar ---
            wd_positions = range(7)
            y_wd_vp = [weekday_vp_counts[i] for i in range(7)]
            y_wd_non_vp = [weekday_non_vp_counts[i] for i in range(7)]
            weekday_axis.bar(wd_positions, y_wd_vp, color="#2ECC71", label="VP Enabled", alpha=0.85)
            weekday_axis.bar(wd_positions, y_wd_non_vp, bottom=y_wd_vp,
                             color="#E74C3C", label="Non-VP (Deficient)", alpha=0.85)
            weekday_axis.set_title("Most Active Days")
            weekday_axis.set_ylabel("Pings")
            weekday_axis.set_xticks(list(wd_positions))
            weekday_axis.set_xticklabels(WEEKDAY_LABELS)
            weekday_axis.grid(axis="y", linestyle="--", alpha=0.25)
            if total_pings > 0:
                weekday_axis.legend(loc="upper right", fontsize=8)
            wd_totals = [y_wd_vp[i] + y_wd_non_vp[i] for i in range(7)]
            if max(wd_totals, default=0) > 0:
                weekday_axis.set_ylim(0, max(wd_totals) + 1)

            # --- Hourly VP/Non-VP stacked bar ---
            hr_positions = range(24)
            y_hr_vp = [hourly_vp_counts[i] for i in range(24)]
            y_hr_non_vp = [hourly_non_vp_counts[i] for i in range(24)]
            hourly_axis.bar(hr_positions, y_hr_vp, color="#2ECC71", label="VP Enabled", alpha=0.85)
            hourly_axis.bar(hr_positions, y_hr_non_vp, bottom=y_hr_vp,
                            color="#E74C3C", label="Non-VP (Deficient)", alpha=0.85)
            hourly_axis.set_title("Most Active Hours (UTC)")
            hourly_axis.set_ylabel("Pings")
            hourly_axis.set_xticks(list(hr_positions))
            hourly_axis.set_xticklabels([f"{h:02d}" for h in hr_positions])
            hourly_axis.grid(axis="y", linestyle="--", alpha=0.25)
            if total_pings > 0:
                hourly_axis.legend(loc="upper right", fontsize=8)
            hr_totals = [y_hr_vp[i] + y_hr_non_vp[i] for i in range(24)]
            if max(hr_totals, default=0) > 0:
                hourly_axis.set_ylim(0, max(hr_totals) + 1)

            figure.suptitle(
                f"Ping Usage Analytics: {filter_name} | Last {n_buckets} {gran_label.lower()}s",
                fontsize=16
            )
            figure.text(
                0.5, 0.94,
                (
                    f"Total Pings: {total_pings} | "
                    f"Active periods: {active_buckets}/{n_buckets} | "
                    f"Peak hour: {most_active_hour_label} | "
                    f"Peak day: {most_active_weekday_label}"
                ),
                ha="center", fontsize=10,
            )
            figure.tight_layout(rect=(0, 0, 1, 0.9))

        image_data = PING_USAGE_TREND_CACHE.get_or_create_bytes(
            {
                "n_buckets": n_buckets,
                "granularity": granularity,
                "filter_group": filter_group,
                "buckets": [b.isoformat() for b in buckets],
                "y_total": y_total,
                "y_vp": y_vp,
                "y_non_vp": y_non_vp,
                "weekday_vp": [weekday_vp_counts[i] for i in range(7)],
                "weekday_non_vp": [weekday_non_vp_counts[i] for i in range(7)],
                "hourly_vp": [hourly_vp_counts[i] for i in range(24)],
                "hourly_non_vp": [hourly_non_vp_counts[i] for i in range(24)],
                "y_rank_vp": y_rank_vp,
                "y_rank_non_vp": y_rank_non_vp,
                "unique_ranks": unique_ranks,
            },
            lambda: render_matplotlib_plot_to_png(plotter),
        )

        discord_file = PING_USAGE_TREND_CACHE.to_discord_file(image_data)

        embed = discord.Embed(
            title=f"Analytics: {filter_name}",
            color=discord.Color.blue(),
            description=(
                f"Overview of `{filter_name}` usage — **{gran_label}** view, "
                f"last **{n_buckets}** periods."
            )
        )
        embed.set_image(url=f"attachment://{PING_USAGE_TREND_CACHE.config.default_filename}")

        embed.add_field(name="Total Volume", value=f"{total_pings} pings")
        embed.add_field(name="Authorization",
                        value=f"✅ {vp_enabled_pings} VP\n❌ {non_vp_pings} Non-VP")
        embed.add_field(name=f"{gran_label} Average", value=f"{avg_per_bucket} pings")
        embed.add_field(name="Peak Day", value=most_active_weekday_label)
        embed.add_field(name="Peak Hour", value=f"{most_active_hour_label} UTC")
        embed.add_field(name="Active Periods", value=f"{active_buckets}/{n_buckets}")

        return embed, discord_file


async def setup(bot: commands.Bot):
    await bot.add_cog(PingUsage(bot))
