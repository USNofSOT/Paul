from datetime import datetime, timedelta
from logging import getLogger

import discord
import numpy as np
from dateutil.relativedelta import relativedelta
from discord import app_commands
from discord.ext import commands
from matplotlib import pyplot as plt

from src.config import IMAGE_CACHES
from src.config.ranks import RANKS
from src.data.repository.role_repository import RoleRepository
from src.security import require_any_role, Role
from src.utils.embeds import error_embed
from src.utils.image_cache import BinaryImageCache, render_matplotlib_plot_to_png

log = getLogger(__name__)

RANK_SIZE_TREND_CACHE = BinaryImageCache(IMAGE_CACHES["rank_size_trend"])

# Granularity options for ranks (no hourly — role sizes are sampled ~daily)
GRANULARITY_OPTIONS = {
    "day":   ("Per Day",   "Break data into individual days"),
    "week":  ("Per Week",  "Break data into calendar weeks"),
    "month": ("Per Month", "Break data into calendar months"),
}

GRANULARITY_DEFAULTS = {
    "day":   30,
    "week":  12,
    "month": 12,
}

GRANULARITY_MAX = {
    "day":   90,
    "week":  52,
    "month": 24,
}

INACTIVE_RANK_NAMES = {"Deckhand", "Recruit", "Retired", "Veteran", "Dungeon Master"}


def _now() -> datetime:
    return datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)


def _bucket_start(dt: datetime, granularity: str) -> datetime:
    if granularity == "day":
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if granularity == "week":
        base = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return base - timedelta(days=base.weekday())
    if granularity == "month":
        return dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    raise ValueError(f"Unknown granularity: {granularity}")


def _generate_buckets(granularity: str, n: int) -> list[datetime]:
    current = _bucket_start(_now(), granularity)
    buckets = []
    for i in range(n - 1, -1, -1):
        if granularity == "day":
            buckets.append(current - timedelta(days=i))
        elif granularity == "week":
            buckets.append(current - relativedelta(weeks=i))
        elif granularity == "month":
            buckets.append(current - relativedelta(months=i))
    return buckets


def _next_bucket(dt: datetime, granularity: str) -> datetime:
    if granularity == "day":
        return dt + timedelta(days=1)
    if granularity == "week":
        return dt + relativedelta(weeks=1)
    if granularity == "month":
        return dt + relativedelta(months=1)
    raise ValueError(f"Unknown granularity: {granularity}")


def _bucket_label(dt: datetime, granularity: str) -> str:
    if granularity == "day":
        return dt.strftime("%d %b")
    if granularity == "week":
        return dt.strftime("%d %b")
    if granularity == "month":
        return dt.strftime("%b '%y")
    return str(dt)


# ---------------------------------------------------------------------------
# Rank membership estimation per bucket
# ---------------------------------------------------------------------------

def _estimate_size_at(sizes: list, bucket_start: datetime, bucket_end: datetime) -> int:
    """
    Return the best member count estimate for a role within [bucket_start, bucket_end].
    Strategy: use the most recent snapshot inside the bucket; fall back to the last
    known snapshot before the bucket.
    """
    in_bucket = [s.member_count for s in sizes if bucket_start <= s.log_time < bucket_end]
    if in_bucket:
        return in_bucket[-1]
    before = [s.member_count for s in sizes if s.log_time < bucket_start]
    return before[-1] if before else 0


# ---------------------------------------------------------------------------
# UI Components
# ---------------------------------------------------------------------------

class RanksFilterSelect(discord.ui.Select):
    def __init__(self, current_filter: str):
        options = [
            discord.SelectOption(label="All Active Ranks",
                                 description="Everyone except Deckhand, Retired, Veteran",
                                 value="active", default=current_filter == "active"),
            discord.SelectOption(label="All Ranks (Including Inactive)",
                                 description="Shows literally every rank historically",
                                 value="all", default=current_filter == "all"),
            discord.SelectOption(label="Able Seaman & Up",
                                 description="Filters out Recruit & Seaman (E3+)",
                                 value="e3_up", default=current_filter == "e3_up"),
            discord.SelectOption(label="NCOs & Up",
                                 description="Filters out all Junior Enlisted (E4+)",
                                 value="nco_up", default=current_filter == "nco_up"),
            discord.SelectOption(label="Senior NCOs & Up",
                                 description="Filters out POs & JPOs (E7+)",
                                 value="snco_up", default=current_filter == "snco_up"),
            discord.SelectOption(label="Officers",
                                 description="Only shows Officers (O1+)",
                                 value="officer", default=current_filter == "officer"),
        ]
        super().__init__(placeholder="Filter by rank group...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: RanksView = self.view
        view.filter_group = self.values[0]
        view.single_rank = None
        embed, discord_file = await view.cog.trend_rank_size(
            interaction, view.n_buckets, view.granularity, view.filter_group, view.single_rank
        )
        view.update_select()
        await interaction.edit_original_response(embed=embed, attachments=[discord_file], view=view)


class RankSingleSelect(discord.ui.Select):
    def __init__(self, current_single: str | None):
        options = [
            discord.SelectOption(
                label="— All (use group filter above) —",
                value="__all__",
                default=current_single is None
            )
        ]
        for rank in RANKS:
            if rank.name == "Dungeon Master":
                continue
            options.append(
                discord.SelectOption(
                    label=rank.name,
                    description=rank.identifier,
                    value=rank.identifier,
                    default=current_single == rank.identifier
                )
            )
        super().__init__(placeholder="Zoom into a single rank...", min_values=1, max_values=1, options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        view: RanksView = self.view
        view.single_rank = None if self.values[0] == "__all__" else self.values[0]
        embed, discord_file = await view.cog.trend_rank_size(
            interaction, view.n_buckets, view.granularity, view.filter_group, view.single_rank
        )
        view.update_select()
        await interaction.edit_original_response(embed=embed, attachments=[discord_file], view=view)


class RanksGranularitySelect(discord.ui.Select):
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
        view: RanksView = self.view
        new_gran = self.values[0]
        if new_gran != view.granularity:
            view.granularity = new_gran
            view.n_buckets = GRANULARITY_DEFAULTS[new_gran]
        embed, discord_file = await view.cog.trend_rank_size(
            interaction, view.n_buckets, view.granularity, view.filter_group, view.single_rank
        )
        view.update_select()
        await interaction.edit_original_response(embed=embed, attachments=[discord_file], view=view)


class RanksView(discord.ui.View):
    def __init__(self, cog: 'Ranks', filter_group: str, n_buckets: int,
                 granularity: str, single_rank: str | None = None):
        super().__init__(timeout=180)
        self.cog = cog
        self.filter_group = filter_group
        self.n_buckets = n_buckets
        self.granularity = granularity
        self.single_rank = single_rank
        self.update_select()

    def update_select(self):
        self.clear_items()
        self.add_item(RanksFilterSelect(self.filter_group))
        self.add_item(RankSingleSelect(self.single_rank))
        self.add_item(RanksGranularitySelect(self.granularity))


# ---------------------------------------------------------------------------
# Cog
# ---------------------------------------------------------------------------

class Ranks(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ranks", description="Get a detailed report of rank sizes over time")
    @app_commands.describe(periods="Number of time periods to show (default varies by granularity)")
    @app_commands.describe(granularity="Time granularity: day, week (default), month")
    @app_commands.describe(hidden="Should only you be able to see the response?")
    @app_commands.choices(granularity=[
        app_commands.Choice(name="Per Day",   value="day"),
        app_commands.Choice(name="Per Week",  value="week"),
        app_commands.Choice(name="Per Month", value="month"),
    ])
    @require_any_role(Role.BOA, Role.NSC_ADMINISTRATOR)
    async def ranks(self, interaction: discord.Interaction,
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

            embed, discord_file = await self.trend_rank_size(
                interaction, n_buckets, granularity, filter_group="active", single_rank=None
            )
            view = RanksView(self, filter_group="active", n_buckets=n_buckets,
                             granularity=granularity, single_rank=None)
            await interaction.followup.send(embed=embed, file=discord_file, view=view)

        except Exception as e:
            log.error(f"Error getting ranks trend: {e}", exc_info=True)
            await interaction.followup.send(
                embed=error_embed("Error generating the ranks trend report."), ephemeral=True
            )

    async def trend_rank_size(self, interaction: discord.Interaction,
                              n_buckets: int, granularity: str,
                              filter_group: str, single_rank: str | None = None):

        buckets = _generate_buckets(granularity, n_buckets)
        gran_label = GRANULARITY_OPTIONS[granularity][0]

        role_repository = RoleRepository()

        series: list[dict] = []
        table_lines: list[str] = []
        current_snapshot: dict[str, int] = {}   # rank_name -> latest member count
        total_tracked_now = 0
        largest_rank_name = ""
        largest_rank_count = 0

        for rank in RANKS:
            # Apply filter
            if single_rank is not None:
                if rank.identifier != single_rank:
                    continue
            else:
                if filter_group == "active" and rank.name in INACTIVE_RANK_NAMES:
                    continue
                elif filter_group == "e3_up" and rank.index < 3:
                    continue
                elif filter_group == "nco_up" and rank.index < 4:
                    continue
                elif filter_group == "snco_up" and rank.index < 6:
                    continue
                elif filter_group == "officer" and rank.index < 9:
                    continue
                if filter_group != "all" and rank.name == "Dungeon Master":
                    continue

            # Load all role-size records for this rank's role IDs
            role_sizes_dict: dict[int, list] = {}
            for role_id in rank.role_ids:
                role_sizes_dict[role_id] = role_repository.get_role_sizes(role_id)

            # Build time series
            y_values: list[int] = []
            for bucket in buckets:
                next_b = _next_bucket(bucket, granularity)
                total = 0
                for role_id in rank.role_ids:
                    total += _estimate_size_at(role_sizes_dict[role_id], bucket, next_b)
                y_values.append(total)

            # Current count = last bucket (most recent)
            current_count = y_values[-1] if y_values else 0
            current_snapshot[rank.name] = current_count
            total_tracked_now += current_count
            table_lines.append(f"`{rank.identifier:<4} - {rank.name:<26}` | **{current_count}**")

            if current_count > largest_rank_count:
                largest_rank_count = current_count
                largest_rank_name = rank.name

            # Delta vs earliest bucket
            earliest = y_values[0] if y_values else 0
            delta = current_count - earliest
            delta_str = f"+{delta}" if delta >= 0 else str(delta)

            # Discord role color
            rank_color = None
            if rank.role_ids:
                first_role_id = next(iter(rank.role_ids))
                discord_role = interaction.guild.get_role(first_role_id)
                if discord_role and discord_role.color.value != 0:
                    rank_color = str(discord_role.color)

            series.append({
                "rank_name": rank.name,
                "identifier": rank.identifier,
                "buckets": buckets,
                "buckets_cache": [b.isoformat() for b in buckets],
                "y_values": y_values,
                "color": rank_color,
                "current_count": current_count,
                "delta": delta,
                "delta_str": delta_str,
            })

        role_repository.close_session()

        # Tick label density
        n = len(buckets)
        tick_step = max(1, n // 20)

        def plotter():
            # Three-panel layout: trend (top), current snapshot bar (middle), net-change bar (bottom)
            figure = plt.figure(figsize=(16, 16))
            grid = figure.add_gridspec(3, 1, height_ratios=[2, 1, 1], hspace=0.45)

            trend_axis = figure.add_subplot(grid[0])
            snapshot_axis = figure.add_subplot(grid[1])
            delta_axis = figure.add_subplot(grid[2])

            labels = [_bucket_label(b, granularity) for b in buckets]
            sparse_labels = [labels[i] if i % tick_step == 0 else "" for i in range(n)]

            # --- Trend lines ---
            for rs in series:
                if sum(rs["y_values"]) == 0:
                    continue
                plot_kwargs = {
                    "marker": "o",
                    "markersize": 4,
                    "label": rs["rank_name"],
                    "linewidth": 2,
                }
                if rs.get("color"):
                    plot_kwargs["color"] = rs["color"]
                trend_axis.plot(range(n), rs["y_values"], **plot_kwargs)

            trend_axis.set_title(f"Rank Size Trend — {gran_label}")
            trend_axis.set_xlabel("Period")
            trend_axis.set_ylabel("Members")
            trend_axis.set_xticks(range(n))
            trend_axis.set_xticklabels(sparse_labels, rotation=45, ha="right", fontsize=8)
            trend_axis.grid(axis="y", linestyle="--", alpha=0.25)
            trend_axis.legend(bbox_to_anchor=(1.01, 1), loc="upper left", fontsize=8)

            # --- Current snapshot bar ---
            snap_names = [rs["rank_name"] for rs in series if rs["current_count"] > 0]
            snap_counts = [rs["current_count"] for rs in series if rs["current_count"] > 0]
            snap_colors = [rs["color"] if rs.get("color") else "#5B9BD5" for rs in series
                           if rs["current_count"] > 0]
            snap_positions = np.arange(len(snap_names))
            bars = snapshot_axis.bar(snap_positions, snap_counts, color=snap_colors, alpha=0.85)
            # Annotate each bar with its count
            for bar, count in zip(bars, snap_counts):
                snapshot_axis.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(snap_counts, default=1) * 0.01,
                    str(count), ha="center", va="bottom", fontsize=7
                )
            snapshot_axis.set_title("Current Member Count per Rank")
            snapshot_axis.set_ylabel("Members")
            snapshot_axis.set_xticks(snap_positions)
            snapshot_axis.set_xticklabels(snap_names, rotation=45, ha="right", fontsize=8)
            snapshot_axis.grid(axis="y", linestyle="--", alpha=0.25)

            # --- Net change bar ---
            delta_names = [rs["rank_name"] for rs in series]
            delta_values = [rs["delta"] for rs in series]
            delta_colors = ["#2ECC71" if d >= 0 else "#E74C3C" for d in delta_values]
            delta_positions = np.arange(len(delta_names))
            delta_axis.bar(delta_positions, delta_values, color=delta_colors, alpha=0.85)
            delta_axis.axhline(0, color="white", linewidth=0.8, alpha=0.5)
            delta_axis.set_title(f"Net Member Change over Last {n_buckets} {gran_label.lower()}s")
            delta_axis.set_ylabel("ΔMembers")
            delta_axis.set_xticks(delta_positions)
            delta_axis.set_xticklabels(delta_names, rotation=45, ha="right", fontsize=8)
            delta_axis.grid(axis="y", linestyle="--", alpha=0.25)

            figure.suptitle(
                f"Rank Size Analytics — {gran_label} | Last {n_buckets} periods",
                fontsize=16
            )
            figure.tight_layout(rect=(0, 0, 0.85, 0.96))

        image_data = RANK_SIZE_TREND_CACHE.get_or_create_bytes(
            {
                "n_buckets": n_buckets,
                "granularity": granularity,
                "filter_group": filter_group,
                "single_rank": single_rank,
                "buckets": [b.isoformat() for b in buckets],
                "series": [
                    {
                        "rank_name": rs["rank_name"],
                        "y_values": rs["y_values"],
                        "color": rs.get("color"),
                        "current_count": rs["current_count"],
                        "delta": rs["delta"],
                    }
                    for rs in series
                ],
            },
            lambda: render_matplotlib_plot_to_png(plotter),
        )

        discord_file = RANK_SIZE_TREND_CACHE.to_discord_file(image_data)

        # ---- Build embed ----
        embed = discord.Embed(
            title="Rank Size Analytics",
            color=discord.Color.blue(),
            description=(
                f"Rank membership report — **{gran_label}** view, "
                f"last **{n_buckets}** periods."
            )
        )
        embed.set_image(url=f"attachment://{RANK_SIZE_TREND_CACHE.config.default_filename}")

        # Stats fields
        growing = sum(1 for rs in series if rs["delta"] > 0)
        shrinking = sum(1 for rs in series if rs["delta"] < 0)
        stable = sum(1 for rs in series if rs["delta"] == 0)

        embed.add_field(name="Total Tracked", value=f"{total_tracked_now} members")
        embed.add_field(name="Largest Rank",
                        value=f"{largest_rank_name} ({largest_rank_count})" if largest_rank_name else "—")
        embed.add_field(name="Trend",
                        value=f"📈 {growing} growing\n📉 {shrinking} shrinking\n➡️ {stable} stable")

        # Current roster table
        if table_lines:
            table_str = "\n".join(table_lines)
            if len(embed.description or "") + len(table_str) + 30 <= 4096:
                embed.description = (embed.description or "") + f"\n\n**Current Roster Check:**\n{table_str}"

        return embed, discord_file


async def setup(bot: commands.Bot):
    await bot.add_cog(Ranks(bot))
