from __future__ import annotations

import asyncio
from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config import NSC_ROLES
from src.config.notifications import NOTIFICATION_ROLLOUT
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.admin.reporting import (
    build_notification_action_embed,
    build_notification_definitions_embed,
    build_notification_overview_embed,
    build_notification_recent_events_embed,
)
from src.notifications.service_factory import NotificationServiceFactory
from src.utils.embeds import error_embed

log = getLogger(__name__)


class NotificationOps(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.notification_service_factory = NotificationServiceFactory(
            rollout_map=NOTIFICATION_ROLLOUT
        )
        self._manual_operation_lock = asyncio.Lock()

    @app_commands.command(
        name="notificationops",
        description="Inspect and operate command inactivity notifications.",
    )
    @app_commands.guild_only()
    @app_commands.checks.has_any_role(*NSC_ROLES)
    @app_commands.checks.cooldown(1, 10.0)
    @app_commands.describe(
        action="Which notification operation to run.",
        hidden="Should only you be able to see the response?",
        recent_limit="How many recent events to include for the recent report.",
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Overview", value="overview"),
            app_commands.Choice(name="Definitions", value="definitions"),
            app_commands.Choice(name="Recent Events", value="recent"),
            app_commands.Choice(name="Run Evaluator", value="run_evaluator"),
            app_commands.Choice(name="Run Worker", value="run_worker"),
        ]
    )
    async def notification_ops(
            self,
            interaction: discord.Interaction,
            action: app_commands.Choice[str],
            hidden: bool = True,
            recent_limit: app_commands.Range[int, 1, 25] = 10,
    ) -> None:
        hidden = hidden or action.value in {"run_evaluator", "run_worker"}
        await interaction.response.defer(
            ephemeral=hidden,
            thinking=True,
        )

        event_repository = NotificationEventRepository()
        sailor_repository = SailorRepository()
        definition_provider = self.notification_service_factory.build_definition_provider()
        try:
            if action.value == "overview":
                embed = build_notification_overview_embed(
                    definition_provider.get_definitions(),
                    event_repository.count_by_status(),
                    event_repository.list_recent_events(limit=5),
                )
            elif action.value == "definitions":
                embed = build_notification_definitions_embed(
                    definition_provider.get_definitions(),
                    NOTIFICATION_ROLLOUT,
                )
            elif action.value == "recent":
                embed = build_notification_recent_events_embed(
                    event_repository.list_recent_events(limit=recent_limit)
                )
            elif action.value == "run_evaluator":
                if self._manual_operation_lock.locked():
                    embed = build_notification_action_embed(
                        "Notification Operation Busy",
                        "Another manual notification operation is already running.",
                    )
                else:
                    async with self._manual_operation_lock:
                        created_events = await self.notification_service_factory.build_scheduler(
                            event_repository=event_repository,
                            sailor_repository=sailor_repository,
                        ).run_for_date(self.bot)
                    embed = build_notification_action_embed(
                        "Notification Evaluator Ran",
                        f"Created **{created_events}** notification event(s) for today.",
                    )
            else:
                if self._manual_operation_lock.locked():
                    embed = build_notification_action_embed(
                        "Notification Operation Busy",
                        "Another manual notification operation is already running.",
                    )
                else:
                    async with self._manual_operation_lock:
                        delivered_count = await self.notification_service_factory.build_worker(
                            event_repository=event_repository,
                            sailor_repository=sailor_repository,
                        ).run_once(self.bot)
                    embed = build_notification_action_embed(
                        "Notification Worker Ran",
                        f"Delivered **{delivered_count}** notification event(s).",
                    )

            await interaction.followup.send(
                embed=embed,
                ephemeral=hidden,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        except Exception as exc:
            log.error("Error running notification ops action %s", action.value, exc_info=True)
            await interaction.followup.send(
                embed=error_embed(
                    title="Notification ops unavailable",
                    description=(
                        "Unable to complete that notification operation right now. "
                        "The failure has been logged."
                    ),
                ),
                ephemeral=True,
                allowed_mentions=discord.AllowedMentions.none(),
            )
        finally:
            event_repository.close_session()
            sailor_repository.close_session()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(NotificationOps(bot))
