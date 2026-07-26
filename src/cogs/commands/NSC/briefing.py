"""NSC commands for private daily and weekly ship briefings."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from src.briefings.delivery import BriefingPeriod, ShipBriefingRunner
from src.config.ships import SHIPS
from src.data.repository.ship_briefing_repository import ShipBriefingRepository
from src.security import Role, audit_interaction, require_any_role
from src.utils.embeds import error_embed

log = logging.getLogger(__name__)


class _EphemeralFollowup:
    def __init__(self, interaction: discord.Interaction) -> None:
        self.followup = interaction.followup

    async def send(self, content=None, **kwargs) -> None:
        await self.followup.send(
            content,
            **kwargs,
            ephemeral=True,
        )


class ShipBriefing(
    commands.GroupCog,
    group_name="briefing",
    group_description="Preview daily and weekly ship briefings.",
):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._lock = asyncio.Lock()

    @app_commands.command(
        name="daily",
        description="Privately preview the daily ship briefing.",
    )
    @app_commands.guild_only()
    @require_any_role(Role.NSC_OBSERVER)
    @audit_interaction
    @app_commands.checks.cooldown(1, 10.0)
    @app_commands.describe(
        ship="Ship to brief; leave empty for every ship.",
    )
    async def daily(
        self,
        interaction: discord.Interaction,
        ship: discord.Role | None = None,
    ) -> None:
        await self._send_ship_briefing(
            interaction,
            period=BriefingPeriod.DAILY,
            ship=ship,
        )

    @app_commands.command(
        name="weekly",
        description="Privately preview the weekly ship briefing.",
    )
    @app_commands.guild_only()
    @require_any_role(Role.NSC_OBSERVER)
    @audit_interaction
    @app_commands.checks.cooldown(1, 10.0)
    @app_commands.describe(
        ship="Ship to brief; leave empty for every ship.",
    )
    async def weekly(
        self,
        interaction: discord.Interaction,
        ship: discord.Role | None = None,
    ) -> None:
        await self._send_ship_briefing(
            interaction,
            period=BriefingPeriod.WEEKLY,
            ship=ship,
        )

    async def _send_ship_briefing(
        self,
        interaction: discord.Interaction,
        *,
        period: BriefingPeriod,
        ship: discord.Role | None,
    ) -> None:
        await interaction.response.defer(ephemeral=True, thinking=True)
        configured_ship_ids = {configured.role_id for configured in SHIPS}
        if ship is not None and ship.id not in configured_ship_ids:
            await interaction.followup.send(
                embed=error_embed(
                    title="Unknown ship",
                    description=(
                        "Choose a configured ship role, or leave ship empty "
                        "to brief every ship."
                    ),
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return
        if self._lock.locked():
            await interaction.followup.send(
                "Another briefing run is already in progress.",
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
            return

        selected_ship_ids = {ship.id} if ship is not None else None
        repository = ShipBriefingRepository()
        try:
            async with self._lock:
                runner = ShipBriefingRunner(
                    repository,
                    production=False,
                    user_mentions_enabled=True,
                )
                message_target = _EphemeralFollowup(interaction)
                summary = await runner.send_briefings(
                    self.bot,
                    period,
                    ship_role_ids=selected_ship_ids,
                    message_target=message_target,
                )
            await interaction.followup.send(
                (
                    f"Prepared **{summary.sent_count}** {period} briefing(s); "
                    f"**{summary.failed_count}** failed."
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception:
            log.exception("Manual ship briefing run failed.")
            await interaction.followup.send(
                embed=error_embed(
                    title="Briefing run failed",
                    description="The run failed and the error has been logged.",
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        finally:
            repository.close_session()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ShipBriefing(bot))
