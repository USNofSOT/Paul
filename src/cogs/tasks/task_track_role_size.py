from logging import getLogger

from discord.ext import commands, tasks

from src.config.main_server import GUILD_ID
from src.config.ranks import RANKS
from src.config.ships import SHIPS
from src.config.task_timing import TRACK_ROLE_SIZE_TASK_TIME
from src.data.models import RoleType
from src.data.repository.role_repository import RoleRepository

log = getLogger(__name__)


class AutoTrackRoleSize(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_track_role_size.start()

    def cog_unload(self):
        self.auto_track_role_size.cancel()

    @tasks.loop(time=TRACK_ROLE_SIZE_TASK_TIME)
    async def auto_track_role_size(self):
        role_repository = RoleRepository()
        try:
            guild = self.bot.get_guild(GUILD_ID)
            if not guild:
                log.error("Could not find guild for tracking role sizes.")
                return

            def track_role(role_id: int, role_type: RoleType, logging_name: str) -> None:
                db_current_role_size = role_repository.get_most_recent_role_size(role_id)
                db_current_size = db_current_role_size.member_count if db_current_role_size else 0

                role = guild.get_role(role_id)
                if role is None:
                    log.warning(f"Role {role_id} for {logging_name} not found in guild.")
                    return

                current_size = len(role.members)

                if db_current_size != current_size:
                    role_repository.save_role_size(role_id, current_size, role_type)
                    log.info(f"Updated size for {role.name} from {db_current_size} to {current_size}")
                else:
                    log.info(f"Size for {role.name} is still {current_size}")

            for rank in RANKS:
                for role_id in rank.role_ids:
                    track_role(role_id, RoleType.RANK, rank.name)

            for ship in SHIPS:
                track_role(ship.role_id, RoleType.SHIP, ship.name)
        
        except Exception as e:
            log.error(f"Error tracking role size: {e}", extra={"notify_engineer": True})
        finally:
            role_repository.close_session()

    @auto_track_role_size.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoTrackRoleSize(bot))
