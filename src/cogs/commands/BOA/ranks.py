from datetime import datetime, timedelta
from logging import getLogger

import discord
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


def _week_anchor_now() -> datetime:
    # Anchor to the beginning of the current week (Monday)
    now = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return now - timedelta(days=now.weekday())


class RanksFilterSelect(discord.ui.Select):
    def __init__(self, current_filter: str):
        options = [
            discord.SelectOption(label="All Active Ranks",
                                 description="Default. Shows everyone except Deckhand, Retired, Veteran",
                                 value="active", default=current_filter == "active"),
            discord.SelectOption(label="All Ranks (Including Inactive)",
                                 description="Shows literally every rank historically", value="all",
                                 default=current_filter == "all"),
            discord.SelectOption(label="Able Seaman & Up", description="Filters out Recruit & Seaman (E3+)",
                                 value="e3_up", default=current_filter == "e3_up"),
            discord.SelectOption(label="NCOs & Up", description="Filters out all Junior Enlisted (E4+)", value="nco_up",
                                 default=current_filter == "nco_up"),
            discord.SelectOption(label="Senior NCOs & Up", description="Filters out POs & JPOs (E7+)", value="snco_up",
                                 default=current_filter == "snco_up"),
            discord.SelectOption(label="Officers", description="Only shows Officers (O1+)", value="officer",
                                 default=current_filter == "officer")
        ]
        super().__init__(placeholder="Filter the graph by rank group...", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        selected_filter = self.values[0]
        view: RanksView = self.view
        view.filter_group = selected_filter

        embed, discord_file = await view.cog.trend_rank_size(interaction, view.weeks, view.filter_group)
        view.update_select()

        # Safely edit ephemeral message via interaction webhook to avoid discord message=None bugs
        await interaction.edit_original_response(embed=embed, attachments=[discord_file], view=view)


class RanksView(discord.ui.View):
    def __init__(self, cog: 'Ranks', filter_group: str, weeks: int):
        super().__init__(timeout=180)
        self.cog = cog
        self.filter_group = filter_group
        self.weeks = weeks
        self.update_select()

    def update_select(self):
        self.clear_items()
        self.add_item(RanksFilterSelect(self.filter_group))


class Ranks(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="ranks", description="Get a report of rank sizes over time")
    @app_commands.describe(weeks="Number of weeks to show trend for (default 12)")
    @app_commands.describe(hidden="Should only you be able to see the response?")
    @require_any_role(Role.BOA, Role.NSC_OBSERVER, Role.NSC_OPERATOR, Role.NSC_ADMINISTRATOR)
    async def ranks(self, interaction: discord.Interaction, weeks: int = 12, hidden: bool = True):
        try:
            await interaction.response.defer(ephemeral=hidden)

            if weeks > 52:
                await interaction.followup.send(embed=error_embed("Cannot trend more than 52 weeks at once."),
                                                ephemeral=True)
                return

            embed, discord_file = await self.trend_rank_size(interaction, weeks, filter_group="active")
            view = RanksView(self, filter_group="active", weeks=weeks)
            await interaction.followup.send(embed=embed, file=discord_file, view=view)

        except Exception as e:
            log.error(f"Error getting ranks trend: {e}", exc_info=True)
            await interaction.followup.send(embed=error_embed("Error generating the ranks trend report."),
                                            ephemeral=True)

    async def trend_rank_size(self, interaction: discord.Interaction, weeks: int, filter_group: str):
        role_repository = RoleRepository()
        embed = discord.Embed(
            title="Rank Size Trend",
            color=discord.Color.blue(),
            description=f"Report for total amount of members per rank over the last {weeks} weeks"
        )

        series = []
        reference_week = _week_anchor_now()

        inactive_rank_names = {"Deckhand", "Recruit", "Retired", "Veteran", "Dungeon Master"}

        table_lines = []

        for rank in RANKS:
            if filter_group == "active" and rank.name in inactive_rank_names:
                continue
            elif filter_group == "e3_up" and rank.index < 3:
                continue
            elif filter_group == "nco_up" and rank.index < 4:
                continue
            elif filter_group == "snco_up" and rank.index < 6:
                continue
            elif filter_group == "officer" and rank.index < 9:
                continue

            # Extra filter to explicitly hide Dungeon Master from up-filters
            if filter_group != "all" and rank.name == "Dungeon Master":
                continue

            x_dates = []
            y_members = []

            # Fetch all role sizes for all role IDs bounded by this rank
            role_sizes_dict = {}
            for role_id in rank.role_ids:
                role_sizes_dict[role_id] = role_repository.get_role_sizes(role_id)

            for week in range(weeks):
                date = reference_week - relativedelta(weeks=week)
                start_date = date
                end_date = (date + relativedelta(weeks=1)) - timedelta(seconds=1)

                total_rank_size_week = 0
                for role_id in rank.role_ids:
                    sizes = role_sizes_dict[role_id]
                    # Find the first matched size in that week
                    size_this_week = [s.member_count for s in sizes if start_date <= s.log_time <= end_date]

                    if size_this_week:
                        total_rank_size_week += size_this_week[0]
                    else:
                        # Fallback to the last known size BEFORE this week
                        last_size_before_week = [s.member_count for s in sizes if s.log_time < start_date]
                        total_rank_size_week += (last_size_before_week[-1] if last_size_before_week else 0)

                x_dates.append(date)
                y_members.append(total_rank_size_week)

            # Current count is the first (latest) value in the week-series
            current_count = y_members[0] if y_members else 0
            table_lines.append(f"`{rank.identifier:<4} - {rank.name:<26}` | **{current_count}**")

            # Grab the Discord role color using the first mapped role ID for this rank
            rank_color = None
            if rank.role_ids:
                # Grab a random role_id from the set natively mapped to the rank
                first_role_id = next(iter(rank.role_ids))
                discord_role = interaction.guild.get_role(first_role_id)
                # Ensure the role exists and has a non-default color actively set
                if discord_role and discord_role.color.value != 0:
                    rank_color = str(discord_role.color)

            series.append(
                {
                    "rank_name": rank.name,
                    "x_dates": x_dates,
                    "x_dates_cache": [date.isoformat() for date in x_dates],
                    "y_values": y_members,
                    "color": rank_color
                }
            )

        def plotter():
            # There are 19 ranks, it will be somewhat congested but visually parsable with a large figure
            plt.figure(figsize=(16, 12))
            plt.title('Rank Size Weekly Trend')
            plt.xlabel('Week')
            plt.ylabel('Members')
            for rank_series in series:
                # If a rank has absolutely zero members plotted over all weeks, optionally skip it to declutter
                if sum(rank_series["y_values"]) > 0:
                    plot_kwargs = {
                        "marker": 'o',
                        "label": rank_series["rank_name"],
                        "linewidth": 2,
                    }
                    if rank_series.get("color"):
                        plot_kwargs["color"] = rank_series["color"]

                    plt.plot(
                        rank_series["x_dates"],
                        rank_series["y_values"],
                        **plot_kwargs
                    )
            # Create a legend positioned outside of the main plot area to prevent overlap
            plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()

        image_data = RANK_SIZE_TREND_CACHE.get_or_create_bytes(
            {
                "weeks": weeks,
                "filter_group": filter_group,
                "reference_week": reference_week.isoformat(),
                "series": [
                    {
                        "rank_name": rs["rank_name"],
                        "x_dates": rs["x_dates_cache"],
                        "y_values": rs["y_values"],
                        "color": rs.get("color"),
                    }
                    for rs in series
                ],
            },
            lambda: render_matplotlib_plot_to_png(plotter),
        )
        discord_file = RANK_SIZE_TREND_CACHE.to_discord_file(image_data)
        embed.set_image(
            url=f"attachment://{RANK_SIZE_TREND_CACHE.config.default_filename}"
        )

        # Add the clean text table showing the latest current member counts
        if table_lines:
            table_str = "\n".join(table_lines)
            if len(table_str) <= 4096:
                embed.description = embed.description + f"\n\n**Current Roster Check:**\n{table_str}"

        role_repository.close_session()
        return embed, discord_file


async def setup(bot: commands.Bot):
    await bot.add_cog(Ranks(bot))
