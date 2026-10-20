from datetime import UTC, datetime
from logging import getLogger

from discord.ext import commands, tasks

from src.briefings.delivery import ShipBriefingRunner
from src.config.briefings import (
    WEEKLY_BRIEFING_ENABLED,
    WEEKLY_BRIEFING_TIME,
    WEEKLY_BRIEFING_WEEKDAY,
)
from src.data.repository.ship_briefing_repository import ShipBriefingRepository

log = getLogger(__name__)


class ShipWeeklyBriefingTask(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ship_weekly_briefing.start()

    def cog_unload(self) -> None:
        self.ship_weekly_briefing.cancel()

    @tasks.loop(time=WEEKLY_BRIEFING_TIME)
    async def ship_weekly_briefing(self) -> None:
        if not WEEKLY_BRIEFING_ENABLED:
            return
        if datetime.now(UTC).weekday() != WEEKLY_BRIEFING_WEEKDAY:
            return
        repository = ShipBriefingRepository()
        try:
            summary = await ShipBriefingRunner(repository).send_weekly_briefings(
                self.bot
            )
            log.info(
                "Weekly ship briefings sent=%s failed=%s.",
                summary.sent_count,
                summary.failed_count,
            )
        finally:
            repository.close_session()

    @ship_weekly_briefing.before_loop
    async def before_ship_weekly_briefing(self) -> None:
        await self.bot.wait_until_ready()

    @ship_weekly_briefing.error
    async def ship_weekly_briefing_error(self, error: Exception) -> None:
        log.error(
            "Weekly ship briefing task stopped unexpectedly.",
            exc_info=error,
            extra={"notify_engineer": True},
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ShipWeeklyBriefingTask(bot))
