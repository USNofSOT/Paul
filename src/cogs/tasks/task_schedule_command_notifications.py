from __future__ import annotations

from logging import getLogger

from discord.ext import commands, tasks

from src.config.task_timing import COMMAND_NOTIFICATION_EVALUATOR_TASK_TIME
from src.data.repository.notification_event_repository import NotificationEventRepository
from src.data.repository.sailor_repository import SailorRepository
from src.notifications.service_factory import NotificationServiceFactory
from src.utils.discord_utils import alert_engineers

log = getLogger(__name__)


class ScheduleCommandNotifications(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.notification_service_factory = NotificationServiceFactory()
        self.evaluate_notifications.start()

    def cog_unload(self) -> None:
        self.evaluate_notifications.cancel()

    @tasks.loop(time=COMMAND_NOTIFICATION_EVALUATOR_TASK_TIME)
    async def evaluate_notifications(self) -> None:
        event_repository = NotificationEventRepository()
        sailor_repository = SailorRepository()
        scheduler = self.notification_service_factory.build_scheduler(
            event_repository=event_repository,
            sailor_repository=sailor_repository,
        )
        try:
            created_events = await scheduler.run_for_date(self.bot)
            log.info("Scheduled %s command inactivity notification events.", created_events)
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
