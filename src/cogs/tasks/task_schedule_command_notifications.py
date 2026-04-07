from __future__ import annotations

import asyncio
import random
from logging import getLogger

from discord.ext import commands, tasks

from src.config.task_timing import (
    COMMAND_NOTIFICATION_EVALUATOR_MAX_INTERVAL_HOURS,
    COMMAND_NOTIFICATION_EVALUATOR_MIN_INTERVAL_HOURS,
)
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.service_factory import NotificationServiceFactory
from src.utils.discord_utils import (
    AlertSeverity,
    EngineerAlertField,
    alert_engineers,
    send_engineer_log,
)

log = getLogger(__name__)


class ScheduleCommandNotifications(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self._random = random.Random()
        self._run_count = 0
        self.notification_service_factory = NotificationServiceFactory()
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
            created_events = await scheduler.run_for_date(self.bot)
            log.info("Scheduled %s command inactivity notification events.", created_events)

            if created_events > 0:
                await send_engineer_log(
                    self.bot,
                    severity=AlertSeverity.INFO,
                    title="Notification Evaluator Results",
                    description="The notification evaluator has finished running and created new events.",
                    fields=(
                        EngineerAlertField("Created Events", f"**{created_events}**"),
                    ),
                )
        except Exception as exc:
            log.error("Error scheduling command inactivity notifications.", exc_info=True)
            await alert_engineers(
                self.bot,
                "Error scheduling command inactivity notifications.",
                exception=exc,
            )
        finally:
            event_repository.close_session()
            sailor_repository.close_session()

    @evaluate_notifications.before_loop
    async def before_evaluate_notifications(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ScheduleCommandNotifications(bot))
