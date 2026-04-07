from __future__ import annotations

from logging import getLogger

from discord.ext import commands, tasks

from src.config.notifications import (
    NOTIFICATION_ROLLOUT,
)
from src.config.task_timing import COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS
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


class ProcessCommandNotifications(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.notification_service_factory = NotificationServiceFactory(
            rollout_map=NOTIFICATION_ROLLOUT
        )
        self.process_notifications.start()

    def cog_unload(self) -> None:
        self.process_notifications.cancel()

    @tasks.loop(seconds=COMMAND_NOTIFICATION_WORKER_TASK_INTERVAL_SECONDS)
    async def process_notifications(self) -> None:
        event_repository = NotificationEventRepository()
        sailor_repository = SailorRepository()
        worker = self.notification_service_factory.build_worker(
            event_repository=event_repository,
            sailor_repository=sailor_repository,
        )
        try:
            delivered_count = await worker.run_once(self.bot)
            if delivered_count:
                log.info("Delivered %s command inactivity notifications.", delivered_count)

                await send_engineer_log(
                    self.bot,
                    severity=AlertSeverity.INFO,
                    title="Notification Worker Results",
                    description="The notification worker has finished a delivery cycle.",
                    fields=(
                        EngineerAlertField("Delivered Notifications", f"**{delivered_count}**"),
                    ),
                )
        except Exception as exc:
            log.error("Error processing command inactivity notifications.", exc_info=True)
            await alert_engineers(
                self.bot,
                "Error processing command inactivity notifications.",
                exception=exc,
            )
        finally:
            event_repository.close_session()
            sailor_repository.close_session()

    @process_notifications.before_loop
    async def before_process_notifications(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ProcessCommandNotifications(bot))
