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

def _week_anchor_now() -> datetime:
    now = utc_time_now().replace(tzinfo=None).replace(hour=0, minute=0, second=0, microsecond=0)
    return now - timedelta(days=now.weekday())

class PingUsageFilterSelect(discord.ui.Select):
    def __init__(self, current_filter: str, guild: discord.Guild):
        options = []
        options.append(
            discord.SelectOption(
                label="All Voyage LFG",
                description="Aggregated view of all Voyage pings.",
                value="ALL",
                default=current_filter == "ALL"
            )
        )
        
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
        selected_filter = self.values[0]
        view: PingUsageView = self.view
        view.filter_group = selected_filter

        embed, discord_file = await view.cog.trend_ping_usage(interaction, view.weeks, view.filter_group)
        view.update_select()
        await interaction.edit_original_response(embed=embed, attachments=[discord_file], view=view)


class PingUsageView(discord.ui.View):
    def __init__(self, cog: 'PingUsage', filter_group: str, weeks: int, guild: discord.Guild):
        super().__init__(timeout=180)
        self.cog = cog
        self.filter_group = filter_group
        self.weeks = weeks
        self.guild = guild
        self.update_select()

    def update_select(self):
        self.clear_items()
        self.add_item(PingUsageFilterSelect(self.filter_group, self.guild))

class PingUsage(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ping_usage", description="Get a report of LFG ping usage and deficiencies over time")
    @app_commands.describe(weeks="Number of weeks to show trend for (default 12)")
    @app_commands.describe(hidden="Should only you be able to see the response?")
    @require_any_role(Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR)
    async def ping_usage(self, interaction: discord.Interaction, weeks: int = 12, hidden: bool = True):
        try:
            await interaction.response.defer(ephemeral=hidden)

            if weeks > 52:
                await interaction.followup.send(embed=error_embed("Cannot trend more than 52 weeks at once."), ephemeral=True)
                return

            default_type = "ALL"
            embed, discord_file = await self.trend_ping_usage(interaction, weeks, filter_group=default_type)
            view = PingUsageView(self, filter_group=default_type, weeks=weeks, guild=interaction.guild)
            await interaction.followup.send(embed=embed, file=discord_file, view=view)

        except Exception as e:
            log.error(f"Error getting ping usage trend: {e}", exc_info=True)
            await interaction.followup.send(embed=error_embed("Error generating the ping usage report."), ephemeral=True)

    async def trend_ping_usage(self, interaction: discord.Interaction, weeks: int, filter_group: str):
        reference_week = _week_anchor_now()
        start_date = reference_week - relativedelta(weeks=weeks)
        
        with PingTrackingRepository() as ping_repo:
            all_logs = ping_repo.get_active_ping_logs_since(start_date)
            
        if filter_group == "ALL":
            logs = all_logs
            filter_name = "All Voyage LFG"
        else:
            role_id = int(filter_group)
            logs = [log_entry for log_entry in all_logs if log_entry.ping_role_id == role_id]
            role = interaction.guild.get_role(role_id)
            filter_name = role.name if role else f"Role {role_id}"
        
        total_pings = len(logs)
        vp_enabled_pings = sum(1 for log_entry in logs if log_entry.has_vp_permission)
        non_vp_pings = total_pings - vp_enabled_pings

        weekly_total = defaultdict(int)
        weekly_vp = defaultdict(int)
        weekly_non_vp = defaultdict(int)
        weekday_counts = {i: 0 for i in range(7)}
        hourly_total_counts = {i: 0 for i in range(24)}
        hourly_vp_counts = {i: 0 for i in range(24)}
        hourly_non_vp_counts = {i: 0 for i in range(24)}
        
        rank_vp_counts = defaultdict(int)
        rank_non_vp_counts = defaultdict(int)
        
        rank_lookup = {}
        for rank in RANKS:
            for role_id in rank.role_ids:
                rank_lookup[role_id] = rank.name
        
        for log_entry in logs:
            base_date = log_entry.created_at.replace(hour=0, minute=0, second=0, microsecond=0)
            if weeks == 1:
                bucket_date = base_date
            else:
                bucket_date = base_date - timedelta(days=base_date.weekday())
            
            weekly_total[bucket_date] += 1
            if log_entry.has_vp_permission:
                weekly_vp[bucket_date] += 1
            else:
                weekly_non_vp[bucket_date] += 1
                
            weekday_counts[log_entry.created_at.weekday()] += 1
            hour = log_entry.created_at.hour
            hourly_total_counts[hour] += 1
            if log_entry.has_vp_permission:
                hourly_vp_counts[hour] += 1
            else:
                hourly_non_vp_counts[hour] += 1
            
            rank_name = rank_lookup.get(log_entry.highest_rank_role_id, "Unknown Rank")
            if log_entry.has_vp_permission:
                rank_vp_counts[rank_name] += 1
            else:
                rank_non_vp_counts[rank_name] += 1

        unique_ranks = list(set(list(rank_vp_counts.keys()) + list(rank_non_vp_counts.keys())))
        unique_ranks.sort(key=lambda r: rank_vp_counts.get(r, 0) + rank_non_vp_counts.get(r, 0), reverse=True)
        
        y_rank_vp = [rank_vp_counts.get(r, 0) for r in unique_ranks]
        y_rank_non_vp = [rank_non_vp_counts.get(r, 0) for r in unique_ranks]

        x_dates = []
        if weeks == 1:
            for day_offset in range(7):
                x_dates.append(reference_week + timedelta(days=day_offset))
        else:
            for week in range(weeks - 1, -1, -1):
                x_dates.append(reference_week - relativedelta(weeks=week))
            
        y_total = [weekly_total.get(d, 0) for d in x_dates]
        y_vp = [weekly_vp.get(d, 0) for d in x_dates]
        y_non_vp = [weekly_non_vp.get(d, 0) for d in x_dates]

        active_weeks = sum(1 for v in y_total if v > 0)
        avg_per_week = round(total_pings / max(weeks, 1), 2)
        avg_per_active_week = round(total_pings / max(active_weeks, 1), 2)
        
        most_active_hour = max(hourly_total_counts.keys(), key=lambda k: hourly_total_counts[k]) if total_pings > 0 else 0
        most_active_weekday = max(weekday_counts.keys(), key=lambda k: weekday_counts[k]) if total_pings > 0 else 0
        
        most_active_hour_label = f"{most_active_hour:02d}:00-{(most_active_hour + 1) % 24:02d}:00"
        most_active_weekday_label = WEEKDAY_LABELS[most_active_weekday]

        def plotter():
            figure = plt.figure(figsize=(16, 15))
            grid = figure.add_gridspec(3, 2, height_ratios=[1.35, 1.35, 1])

            weekly_axis = figure.add_subplot(grid[0, :])
            rank_axis = figure.add_subplot(grid[1, :])
            weekday_axis = figure.add_subplot(grid[2, 0])
            hourly_axis = figure.add_subplot(grid[2, 1])

            weekly_positions = range(len(x_dates))
            weekly_labels_str = [d.strftime("%d %b") for d in x_dates]

            # Bar chart for Total Pings
            weekly_axis.bar(
                weekly_positions,
                y_total,
                color="#8CB9D1",
                label="Total Pings",
                alpha=0.4
            )
            
            # Line chart overlay for VP vs Non-VP
            if total_pings > 0:
                weekly_axis.plot(
                    list(weekly_positions),
                    y_vp,
                    color="#2ECC71",
                    marker="o",
                    linewidth=3,
                    markersize=8,
                    label="VP Enabled"
                )
                weekly_axis.plot(
                    list(weekly_positions),
                    y_non_vp,
                    color="#E74C3C",
                    marker="o",
                    linewidth=3,
                    markersize=8,
                    label="Non-VP (Deficient)"
                )
                
            if weeks == 1:
                weekly_axis.set_title(f"Daily Pings Overview: {filter_name}")
                weekly_axis.set_xlabel("Day")
            else:
                weekly_axis.set_title(f"Weekly Pings Overview: {filter_name}")
                weekly_axis.set_xlabel("Week Starting")
                
            weekly_axis.set_ylabel("Pings")
            weekly_axis.set_xticks(list(weekly_positions))
            weekly_axis.set_xticklabels(weekly_labels_str, rotation=45, ha="right", fontsize=8)
            weekly_axis.grid(axis="y", linestyle="--", alpha=0.25)
            weekly_axis.legend(loc="upper left")

            # Rank Distribution Stacked Bar Chart
            if unique_ranks:
                rank_positions = np.arange(len(unique_ranks))
                rank_axis.bar(
                    rank_positions,
                    y_rank_vp,
                    color="#2ECC71",
                    label="VP Enabled",
                    alpha=0.8
                )
                rank_axis.bar(
                    rank_positions,
                    y_rank_non_vp,
                    bottom=y_rank_vp,
                    color="#E74C3C",
                    label="Non-VP (Deficient)",
                    alpha=0.8
                )
                rank_axis.set_title(f"Rank Distribution: {filter_name}")
                rank_axis.set_ylabel("Pings")
                rank_axis.set_xticks(rank_positions)
                rank_axis.set_xticklabels(unique_ranks, rotation=45, ha="right", fontsize=8)
                rank_axis.grid(axis="y", linestyle="--", alpha=0.25)
                rank_axis.legend(loc="upper right")
            else:
                rank_axis.set_title(f"Rank Distribution: {filter_name}")
                rank_axis.text(0.5, 0.5, "No rank data available", ha="center", va="center")

            # Weekday Bar Chart
            weekday_positions = range(7)
            y_weekday = [weekday_counts[i] for i in range(7)]
            weekday_axis.bar(
                weekday_positions,
                y_weekday,
                color="#ff7f0e",
            )
            weekday_axis.set_title("Most Active Days")
            weekday_axis.set_ylabel("Pings")
            weekday_axis.set_xticks(list(weekday_positions))
            weekday_axis.set_xticklabels(WEEKDAY_LABELS)
            weekday_axis.grid(axis="y", linestyle="--", alpha=0.25)

            # Hourly Bar Chart
            hourly_positions = range(24)
            y_hourly_vp = [hourly_vp_counts[i] for i in range(24)]
            y_hourly_non_vp = [hourly_non_vp_counts[i] for i in range(24)]
            
            hourly_axis.bar(
                hourly_positions,
                y_hourly_vp,
                color="#2ECC71",
                label="VP Enabled",
                alpha=0.8
            )
            hourly_axis.bar(
                hourly_positions,
                y_hourly_non_vp,
                bottom=y_hourly_vp,
                color="#E74C3C",
                label="Non-VP (Deficient)",
                alpha=0.8
            )
            hourly_axis.set_title("Most Active Hours (UTC)")
            hourly_axis.set_ylabel("Pings")
            hourly_axis.set_xticks(list(hourly_positions))
            hourly_axis.set_xticklabels([f"{hour:02d}" for hour in hourly_positions])
            hourly_axis.grid(axis="y", linestyle="--", alpha=0.25)
            if total_pings > 0:
                hourly_axis.legend(loc="upper right")

            if max(hourly_total_counts.values(), default=0) > 0:
                hourly_axis.set_ylim(0, max(hourly_total_counts.values()) + 1)
            if max(y_weekday, default=0) > 0:
                weekday_axis.set_ylim(0, max(y_weekday) + 1)

            figure.suptitle(f"Ping Usage Analytics: {filter_name} | Last {weeks} weeks", fontsize=16)
            figure.text(
                0.5,
                0.94,
                (
                    f"Total Pings: {total_pings} | "
                    f"Active weeks: {active_weeks}/{weeks} | "
                    f"Peak hour: {most_active_hour_label} | "
                    f"Peak day: {most_active_weekday_label}"
                ),
                ha="center",
                fontsize=10,
            )
            figure.tight_layout(rect=(0, 0, 1, 0.9))

        # Because we changed the structure heavily, we should change the cache keys
        image_data = PING_USAGE_TREND_CACHE.get_or_create_bytes(
            {
                "weeks": weeks,
                "filter_group": filter_group,
                "reference_week": reference_week.isoformat(),
                "y_total": y_total,
                "y_vp": y_vp,
                "y_non_vp": y_non_vp,
                "weekday_counts": [weekday_counts[i] for i in range(7)],
                "hourly_vp_counts": [hourly_vp_counts[i] for i in range(24)],
                "hourly_non_vp_counts": [hourly_non_vp_counts[i] for i in range(24)],
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
            description=f"Overview of `{filter_name}` usage over the last {weeks} weeks."
        )
        embed.set_image(url=f"attachment://{PING_USAGE_TREND_CACHE.config.default_filename}")
        
        embed.add_field(name="Total Volume", value=f"{total_pings} pings")
        embed.add_field(name="Authorization", value=f"✅ {vp_enabled_pings} VP\n❌ {non_vp_pings} Non-VP")
        embed.add_field(name="Weekly Average", value=f"{avg_per_week} pings/wk")
        embed.add_field(name="Peak Day", value=most_active_weekday_label)
        embed.add_field(name="Peak Hour", value=f"{most_active_hour_label} UTC")

        return embed, discord_file


async def setup(bot: commands.Bot):
    await bot.add_cog(PingUsage(bot))
