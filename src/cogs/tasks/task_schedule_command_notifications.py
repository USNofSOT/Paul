from __future__ import annotations

import asyncio
import random
from logging import getLogger

from discord.ext import commands, tasks

from src.config.notifications import NOTIFICATION_LOOKAHEAD_HOURS
from src.config.task_timing import (
    COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS,
    COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS,
)
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.admin.engineer_overview import build_ship_overview_field
from src.notifications.service_factory import NotificationServiceFactory
from src.utils.discord_utils import (
    AlertSeverity,
    EngineerAlertField,
    send_engineer_log,
)

log = getLogger(__name__)


class ScheduleCommandNotifications(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._random = random.Random()
        self._run_count = 0
        self.notification_service_factory = NotificationServiceFactory()
        log.info(
            "[NOTIFICATIONS] Scheduler task initialised: every %s-%sh with %sh lookahead.",
            COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS,
            COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS,
            NOTIFICATION_LOOKAHEAD_HOURS,
        )
        self.evaluate_notifications.start()

    def cog_unload(self) -> None:
        self.evaluate_notifications.cancel()

    def _sample_additional_delay_seconds(self) -> float:
        max_additional_hours = (
            COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS
            - COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS
        )
        return self._random.uniform(0.0, max_additional_hours * 60 * 60)

    @tasks.loop(hours=COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS)
    async def evaluate_notifications(self) -> None:
        is_first_run = self._run_count == 0
        self._run_count += 1

        if not is_first_run:
            additional_delay_seconds = self._sample_additional_delay_seconds()
            log.info(
                "Delaying command inactivity notification evaluation by %.0f seconds.",
                additional_delay_seconds,
            )
            await asyncio.sleep(additional_delay_seconds)

        event_repository = NotificationEventRepository()
        sailor_repository = SailorRepository()
        scheduler = self.notification_service_factory.build_scheduler(
            event_repository=event_repository,
            sailor_repository=sailor_repository,
        )
        try:
            run_summary = await scheduler.run_once(self.bot)
            created_events = run_summary.event_count
            log.info("Scheduled %s command inactivity notification events.", created_events)

            fields = [EngineerAlertField("Created Events", f"**{created_events}**")]
            ship_overview_field = build_ship_overview_field(run_summary.per_ship_counts)
            if ship_overview_field is not None:
                fields.append(ship_overview_field)

            if created_events > 0:
                await send_engineer_log(
                    self.bot,
                    severity=AlertSeverity.INFO,
                    title="Notification Evaluator Results",
                    description="The notification evaluator has finished running and created new events.",
                    fields=tuple(fields),
                )
        except Exception as exc:
            log.error("Error scheduling command inactivity notifications: %s", exc, exc_info=True,
                      extra={"notify_engineer": True})
        finally:
            event_repository.close_session()
            sailor_repository.close_session()

    @evaluate_notifications.before_loop
    async def before_evaluate_notifications(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ScheduleCommandNotifications(bot))