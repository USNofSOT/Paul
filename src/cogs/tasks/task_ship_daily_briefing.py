from logging import getLogger

from discord.ext import commands, tasks

from src.briefings.delivery import ShipBriefingRunner
from src.config.briefings import DAILY_BRIEFING_ENABLED, DAILY_BRIEFING_TIME
from src.data.repository.ship_briefing_repository import ShipBriefingRepository

log = getLogger(__name__)


class ShipDailyBriefingTask(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.ship_daily_briefing.start()

    def cog_unload(self) -> None:
        self.ship_daily_briefing.cancel()

    @tasks.loop(time=DAILY_BRIEFING_TIME)
    async def ship_daily_briefing(self) -> None:
        if not DAILY_BRIEFING_ENABLED:
            return
        repository = ShipBriefingRepository()
        try:
            summary = await ShipBriefingRunner(repository).send_daily_briefings(
                self.bot
            )
            log.info(
                "Daily ship briefings sent=%s failed=%s.",
                summary.sent_count,
                summary.failed_count,
            )
        finally:
            repository.close_session()

    @ship_daily_briefing.before_loop
    async def before_ship_daily_briefing(self) -> None:
        await self.bot.wait_until_ready()

    @ship_daily_briefing.error
    async def ship_daily_briefing_error(self, error: Exception) -> None:
        log.error(
            "Daily ship briefing task stopped unexpectedly.",
            exc_info=error,
            extra={"notify_engineer": True},
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ShipDailyBriefingTask(bot))
