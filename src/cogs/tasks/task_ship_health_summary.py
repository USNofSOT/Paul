from __future__ import annotations

from datetime import datetime
from logging import getLogger

from discord.ext import commands, tasks
from matplotlib.dates import UTC

from src.config.notifications import SHIP_HEALTH_SUMMARY_ENABLED
from src.config.task_timing import (
    SHIP_HEALTH_SUMMARY_TASK_TIME,
    SHIP_HEALTH_SUMMARY_TASK_WEEKDAY,
)
from src.data.repository.ship_health_summary_repository import ShipHealthSummaryRepository
from src.notifications.service_factory import NotificationServiceFactory

log = getLogger(__name__)


class ShipHealthSummaryTask(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.notification_service_factory = NotificationServiceFactory()
        log.info(
            "[SHIP_HEALTH] Weekly task initialised: weekday=%s time=%s enabled=%s.",
            SHIP_HEALTH_SUMMARY_TASK_WEEKDAY,
            SHIP_HEALTH_SUMMARY_TASK_TIME.isoformat(),
            SHIP_HEALTH_SUMMARY_ENABLED,
        )
        self.ship_health_summary.start()

    def cog_unload(self) -> None:
        self.ship_health_summary.cancel()

    @tasks.loop(time=SHIP_HEALTH_SUMMARY_TASK_TIME)
    async def ship_health_summary(self) -> None:
        if not SHIP_HEALTH_SUMMARY_ENABLED:
            return

        if datetime.now(UTC).weekday() != SHIP_HEALTH_SUMMARY_TASK_WEEKDAY:
            return

        repository = ShipHealthSummaryRepository()
        service = self.notification_service_factory.build_ship_health_summary_service(
            repository=repository,
        )
        try:
            run_summary = await service.run_once(self.bot)
            log.info(
                "Weekly ship health summaries sent=%s skipped=%s.",
                run_summary.summary_count,
                run_summary.skipped_count,
            )
        except Exception as exc:
            log.error("Error sending weekly ship health summaries: %s", exc, exc_info=True,
                      extra={"notify_engineer": True})
        finally:
            repository.close_session()

    @ship_health_summary.before_loop
    async def before_ship_health_summary(self) -> None:
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ShipHealthSummaryTask(bot))
