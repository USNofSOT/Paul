from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from src.config import IMAGE_CACHES
from src.config.pocket_watch import POCKET_WATCH_DEFAULT_DAYS
from src.config.ranks_roles import JE_AND_UP
from src.core.command_cooldowns import handle_app_command_cooldown_error
from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.embeds import default_embed, error_embed
from src.utils.image_cache import BinaryImageCache
from src.utils.pocket_watch import (
    DEFAULT_POCKET_WATCH_THRESHOLDS,
    PocketWatchError,
    PocketWatchInsufficientDataError,
    analyze_pocket_watch_activity,
    render_pocket_watch_chart,
    validate_days,
)

log = logging.getLogger(__name__)

POCKET_WATCH_ACTIVITY_CACHE = BinaryImageCache(
    IMAGE_CACHES["pocket_watch_activity_chart"]
)


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
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def pocket_watch(
            self,
            interaction: discord.Interaction,
            target: discord.Member | None = None,
            days: int = POCKET_WATCH_DEFAULT_DAYS,
    ) -> None:
        await interaction.response.defer(ephemeral=True)

        target = target or interaction.user
        display_name = target.display_name or target.name
        sailor_repository: SailorRepository | None = None
        voyage_repository: VoyageRepository | None = None
        hosted_repository: HostedRepository | None = None

        try:
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
                title="Pocket Watch",
                description=(
                    f"Voyage activity analysis for {target.mention} over the "
                    f"last {days} days."
                ),
                author=False,
            )
            embed.set_thumbnail(url=target.display_avatar.url)

            embed.add_field(
                name="Attendance",
                value=(
                    f"**{analysis.total_voyages}** attended voyages\n"
                    f"**{analysis.active_weeks}/{analysis.total_weeks}** active weeks\n"
                    f"**{analysis.average_voyages_per_week:.2f}** voyages per week\n"
                    f"**{analysis.average_voyages_per_active_week:.2f}** per "
                    "active week"
                ),
                inline=True,
            )
            embed.add_field(
                name="Peak Activity",
                value=(
                    f"**{analysis.most_active_weekday_label}** is the busiest day\n"
                    f"**{analysis.most_active_hour_label}** is the busiest hour block\n"
                    f"Timezone: **{analysis.timezone_label}**"
                ),
                inline=True,
            )
            embed.add_field(
                name="Window",
                value=(
                    "First voyage: "
                    f"**{analysis.first_voyage_at.strftime('%Y-%m-%d %H:%M')}**\n"
                    "Last voyage: "
                    f"**{analysis.last_voyage_at.strftime('%Y-%m-%d %H:%M')}**"
                ),
                inline=False,
            )

            if analysis.hosted_activity_present:
                embed.add_field(
                    name="Hosting",
                    value=(
                        f"Hosted **{analysis.total_hosted}** voyage"
                        f"{'s' if analysis.total_hosted != 1 else ''} in the "
                        "same period.\n"
                        "Hosting is shown as the orange overlay on the weekly chart."
                    ),
                    inline=False,
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
        if await handle_app_command_cooldown_error(interaction, error):
            return

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
