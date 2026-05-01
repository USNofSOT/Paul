import logging
import discord
from discord.ext import commands

from src.config.ping_tracking import PING_TRACKING_CONFIG
from src.data.repository.ping_tracking_repository import PingTrackingRepository

log = logging.getLogger(__name__)

class OnRawMessageDeletePingTracker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        # Verify if the channel is tracked
        if payload.channel_id not in PING_TRACKING_CONFIG:
            return

        with PingTrackingRepository() as ping_repo:
            try:
                affected_rows = ping_repo.mark_as_deleted(payload.message_id)
                if affected_rows > 0:
                    log.info(f"[{payload.message_id}] Marked {affected_rows} ping logs as deleted.")
            except Exception as e:
                log.error(f"[{payload.message_id}] Error marking ping logs as deleted: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnRawMessageDeletePingTracker(bot))
