import logging
import uuid
import discord
from discord.ext import commands

from src.config.ping_tracking import PING_TRACKING_CONFIG
from src.config.ranks_roles import VOYAGE_PERMISSIONS
from src.data.repository.ping_tracking_repository import PingTrackingRepository
from src.utils.rank_and_promotion_utils import get_current_rank
from src.utils.ship_utils import get_ship_role_id_by_member

log = logging.getLogger(__name__)

class OnMessagePingTracker(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return

        channel_config = PING_TRACKING_CONFIG.get(message.channel.id)
        if not channel_config:
            return

        # Find mentioned roles in the message that are tracked
        tracked_pings = [
            {"role_id": r.id, "ping_type": channel_config[r.id]}
            for r in message.role_mentions if r.id in channel_config
        ]

        if not tracked_pings:
            return

        member = message.author
        if not isinstance(member, discord.Member):
            return

        # Gather user snapshot
        current_rank = get_current_rank(member)
        highest_rank_role_id = next((r.id for r in member.roles if r.id in current_rank.role_ids), None) if current_rank else None

        ship_role_id = get_ship_role_id_by_member(member)
        if ship_role_id is not None and ship_role_id < 0:
            ship_role_id = None

        has_vp = any(r.id == VOYAGE_PERMISSIONS for r in member.roles)

        pings_data = [
            {
                "id": str(uuid.uuid4()),
                "user_id": member.id,
                "channel_id": message.channel.id,
                "message_id": message.id,
                "ping_role_id": ping["role_id"],
                "ping_type": ping["ping_type"],
                "highest_rank_role_id": highest_rank_role_id,
                "ship_role_id": ship_role_id,
                "has_vp_permission": has_vp
            }
            for ping in tracked_pings
        ]

        with PingTrackingRepository() as ping_repo:
            try:
                ping_repo.log_pings_bulk(pings_data)
                log.debug(f"[{message.id}] Logged {len(pings_data)} role pings via bulk insert.")
            except Exception as e:
                log.error(f"[{message.id}] Error logging role pings: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(OnMessagePingTracker(bot))
