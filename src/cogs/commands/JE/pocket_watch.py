from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from src.config.cache import IMAGE_CACHES
from src.config.pocket_watch import POCKET_WATCH_DEFAULT_DAYS
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.security import require_any_role, Role, resolve_effective_roles
from src.utils.embeds import default_embed, error_embed
from src.utils.image_cache import BinaryImageCache
from src.utils.pocket_watch import DEFAULT_POCKET_WATCH_THRESHOLDS, validate_days, analyze_pocket_watch_activity, \
    render_pocket_watch_chart, PocketWatchInsufficientDataError, PocketWatchError

log = logging.getLogger(__name__)

POCKET_WATCH_ACTIVITY_CACHE = BinaryImageCache(
    IMAGE_CACHES["pocket_watch_activity_chart"]
)
EMBED_FIELD_SPACER = "\u200b"


def _format_activity_timestamp(value: datetime | None) -> str:
    if value is None:
        return "No activity"
    return discord.utils.format_dt(value, style="f")


def _format_hour_block_timestamp(
        reference_time: datetime | None,
        hour: int | None,
) -> str:
    if reference_time is None or hour is None:
        return "No activity"

    start_time = reference_time.replace(
        hour=hour,
        minute=0,
        second=0,
        microsecond=0,
    )
    end_time = start_time + timedelta(hours=1)
    return (
        f"{discord.utils.format_dt(start_time, style='t')} - "
        f"{discord.utils.format_dt(end_time, style='t')}"
    )


def _build_activity_volume_field(
        *,
        total_events: int,
        weeks_label: str,
        active_weeks: int,
        total_weeks: int,
        average_per_week: float,
        average_per_active_week: float,
) -> str:
    return (
        f"Total: **{total_events}**\n"
        f"{weeks_label}: **{active_weeks}/{total_weeks}**\n"
        f"Avg / week: **{average_per_week:.2f}**\n"
        f"Avg / active: **{average_per_active_week:.2f}**"
    )


def _build_activity_patterns_field(
        *,
        busiest_day: str,
        busiest_hour: str,
        first_seen: datetime | None,
        last_seen: datetime | None,
        empty_label: str,
) -> str:
    if first_seen is None or last_seen is None:
        return empty_label

    return (
        f"Peak day: **{busiest_day}**\n"
        f"Peak hour: **{busiest_hour}**\n"
        # f"First: **{_format_activity_timestamp(first_seen)}**\n"
        # f"Last: **{_format_activity_timestamp(last_seen)}**"
    )


def _add_field_pair(
        embed: discord.Embed,
        *,
        left_name: str,
        left_value: str,
        right_name: str,
        right_value: str,
) -> None:
    embed.add_field(name=left_name, value=left_value, inline=True)
    embed.add_field(name=right_name, value=right_value, inline=True)


def _can_view_other_target(member: discord.abc.User | discord.Member) -> bool:
    if not isinstance(member, discord.Member):
        return False

    user_roles = resolve_effective_roles(member)
    return Role.NCO in user_roles


class PocketWatch(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="pocketwatch",
        description="Analyze a sailor's voyage activity over time",
    )
    @app_commands.describe(
        target="The sailor to analyze. Defaults to yourself.",
        days=f"Time window in days. Defaults to {POCKET_WATCH_DEFAULT_DAYS}.",
    )
    @require_any_role(Role.JE)
    async def pocket_watch(
            self,
            interaction: discord.Interaction,
            target: discord.Member | None = None,
            days: int = POCKET_WATCH_DEFAULT_DAYS,
    ) -> None:
        await interaction.response.defer(ephemeral=False)

        target = target or interaction.user
        display_name = target.display_name or target.name
        sailor_repository: SailorRepository | None = None
        voyage_repository: VoyageRepository | None = None
        hosted_repository: HostedRepository | None = None

        try:
            if target.id != interaction.user.id and not _can_view_other_target(
                    interaction.user
            ):
                await interaction.followup.send(
                    embed=error_embed(
                        title="Pocket Watch Access Denied",
                        description=(
                            "You can view your own pocket watch, but inspecting "
                            "another sailor requires `NCO+`."
                        ),
                        footer=False,
                    ),
                    ephemeral=True,
                )
                return

            validate_days(days, DEFAULT_POCKET_WATCH_THRESHOLDS)
            sailor_repository = SailorRepository()
            voyage_repository = VoyageRepository()
            hosted_repository = HostedRepository()
            sailor = sailor_repository.get_sailor(target.id)
            now = datetime.now(UTC)
            start_date = now - timedelta(days=days)
            query_start_date = start_date.replace(tzinfo=None)
            query_end_date = now.replace(tzinfo=None)

            attended_voyages = (
                voyage_repository.get_voyages_by_target_ids_and_between_dates(
                    [target.id],
                    query_start_date,
                    query_end_date,
                )
            )
            hosted_entries = (
                hosted_repository.get_hosted_by_target_ids_and_between_dates(
                    [target.id],
                    query_start_date,
                    query_end_date,
                )
            )

            analysis = analyze_pocket_watch_activity(
                attended_voyages,
                hosted_entries,
                days=days,
                timezone_value=sailor.timezone if sailor else None,
                thresholds=DEFAULT_POCKET_WATCH_THRESHOLDS,
                now=now,
            )

            image_data = await POCKET_WATCH_ACTIVITY_CACHE.get_or_create_bytes_async(
                analysis.cache_payload(
                    target_id=target.id,
                    days=days,
                    display_name=display_name,
                ),
                lambda: render_pocket_watch_chart(
                    analysis,
                    display_name=display_name,
                    days=days,
                ),
            )

            embed = default_embed(
                title="Pocket Watch Report",
                description=(
                    f"Activity report for {target.mention} over the last "
                    f"**{days}** days."
                ),
                author=False,
            )
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.timestamp = now

            embed.add_field(
                name="🧭 Window",
                value=(
                    f"Start: {_format_activity_timestamp(analysis.window_start)}\n"
                    f"End: {_format_activity_timestamp(analysis.window_end)}\n"
                    f"Timezone: **{analysis.timezone_label}**"
                ),
                inline=False,
            )

            embed.add_field(
                name=EMBED_FIELD_SPACER,
                value=EMBED_FIELD_SPACER,
                inline=False,
            )

            _add_field_pair(
                embed,
                left_name="📘 Attended Voyages",
                left_value=_build_activity_volume_field(
                    total_events=analysis.total_voyages,
                    weeks_label="Weeks active",
                    active_weeks=analysis.active_weeks,
                    total_weeks=analysis.total_weeks,
                    average_per_week=analysis.average_voyages_per_week,
                    average_per_active_week=analysis.average_voyages_per_active_week,
                ),
                right_name="📊 Attendance Patterns",
                right_value=_build_activity_patterns_field(
                    busiest_day=analysis.most_active_weekday_label,
                    busiest_hour=_format_hour_block_timestamp(
                        analysis.first_voyage_at,
                        analysis.most_active_hour,
                    ),
                    first_seen=analysis.first_voyage_at,
                    last_seen=analysis.last_voyage_at,
                    empty_label="No attended voyages were logged in this period.",
                ),
            )

            if analysis.hosted_activity_present:
                embed.add_field(
                    name=EMBED_FIELD_SPACER,
                    value=EMBED_FIELD_SPACER,
                    inline=False,
                )
                _add_field_pair(
                    embed,
                    left_name="🟧 Hosted Voyages",
                    left_value=_build_activity_volume_field(
                        total_events=analysis.total_hosted,
                        weeks_label="Weeks active",
                        active_weeks=analysis.active_hosted_weeks,
                        total_weeks=analysis.total_weeks,
                        average_per_week=analysis.average_hosted_per_week,
                        average_per_active_week=analysis.average_hosted_per_active_week,
                    ),
                    right_name="🕒 Hosting Patterns",
                    right_value=_build_activity_patterns_field(
                        busiest_day=analysis.most_active_hosted_weekday_label,
                        busiest_hour=_format_hour_block_timestamp(
                            analysis.first_hosted_at,
                            analysis.most_active_hosted_hour,
                        ),
                        first_seen=analysis.first_hosted_at,
                        last_seen=analysis.last_hosted_at,
                        empty_label="No hosted voyages were logged in this period.",
                    ),
                )

            if image_data is not None:
                chart_file = POCKET_WATCH_ACTIVITY_CACHE.to_discord_file(image_data)
                embed.set_image(
                    url=(
                        "attachment://"
                        f"{POCKET_WATCH_ACTIVITY_CACHE.config.default_filename}"
                    )
                )
                await interaction.followup.send(
                    embed=embed,
                    file=chart_file,
                    ephemeral=True,
                )
                return

            await interaction.followup.send(embed=embed, ephemeral=True)
        except PocketWatchInsufficientDataError as error:
            await interaction.followup.send(
                embed=error_embed(
                    title="Pocket Watch Unavailable",
                    description=str(error),
                    footer=False,
                ),
                ephemeral=True,
            )
        except PocketWatchError as error:
            await interaction.followup.send(
                embed=error_embed(
                    title="Invalid Pocket Watch Request",
                    description=str(error),
                    footer=False,
                ),
                ephemeral=True,
            )
        except Exception as error:
            log.error("Error running pocket watch command: %s", error, exc_info=True)
            await interaction.followup.send(
                embed=error_embed(
                    title="Pocket Watch Failed",
                    description=(
                        "An unexpected error occurred while building the pocket "
                        "watch view."
                    ),
                    exception=error,
                ),
                ephemeral=True,
            )
        finally:
            if sailor_repository is not None:
                sailor_repository.close_session()
            if voyage_repository is not None:
                voyage_repository.close_session()
            if hosted_repository is not None:
                hosted_repository.close_session()

    @pocket_watch.error
    async def pocket_watch_error(
            self,
            interaction: discord.Interaction,
            error: app_commands.AppCommandError,
    ) -> None:
        if isinstance(error, app_commands.errors.MissingAnyRole):
            responder = (
                interaction.followup.send
                if interaction.response.is_done()
                else interaction.response.send_message
            )
            await responder(
                embed=error_embed(
                    title="Pocket Watch Access Denied",
                    description=(
                        "You do not have the required permissions to use this "
                        "command."
                    ),
                    footer=False,
                ),
                ephemeral=True,
            )
            return

        await (
            interaction.followup.send
            if interaction.response.is_done()
            else interaction.response.send_message
        )(
            embed=error_embed(
                title="Pocket Watch Failed",
                description="Unable to process the pocket watch command right now.",
            ),
            ephemeral=True,
        )
        log.error("Pocket watch app command error: %s", error, exc_info=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(PocketWatch(bot))
