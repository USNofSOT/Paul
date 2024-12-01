import datetime
from logging import getLogger

from discord.ext import commands, tasks

from src.config.main_server import GUILD_ID
from src.config.ships import SHIPS
from src.data.repository.ship_repository import ShipRepository

log = getLogger(__name__)

class AutoTrackShipSize(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.auto_track_ship_size.start()

    def cog_unload(self):
        self.auto_track_ship_size.cancel()


    @tasks.loop(time=datetime.time(hour=0, minute=00, tzinfo=datetime.timezone.utc))
    async def auto_track_ship_size(self):
        ship_repository = ShipRepository()
        try:
            for ship in SHIPS:
                db_current_ship_size = ship_repository.get_most_recent_ship_size(ship.role_id)
                if db_current_ship_size is None:
                    db_current_ship_size = 0
                else:
                    db_current_ship_size = db_current_ship_size.member_count
                role = self.bot.get_guild(GUILD_ID).get_role(ship.role_id)
                current_ship_size = len(role.members)

                if db_current_ship_size != current_ship_size:
                    ship_repository.save_ship_size(ship.role_id, current_ship_size)
                    log.info(f"Updated ship size for {role.name} from {db_current_ship_size} to {current_ship_size}")
                else:
                    log.info(f"Ship size for {role.name} is still {current_ship_size}")
        except Exception as e:
            log.error(f"Error tracking ship")
        finally:
            ship_repository.close_session()

    @auto_track_ship_size.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoTrackShipSize(bot))