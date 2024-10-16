import discord
import logging
from discord.ext import commands
from src.config import NCO_COMMS, ENGINE_ROOM, GUILD_ID, SPD_ID

log = logging.getLogger(__name__)

class BotDown(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="botdown")
    async def botdown(self, ctx):
        """Sends an LOA notification to the specified channels."""
        main_guild = GUILD_ID
        spd_guild = SPD_ID
        
        if main_guild:
            nco_coms_channel = main_guild.get_channel(NCO_COMMS)
            if nco_coms_channel:
                await nco_coms_channel.send("I'm going on LOA, be back soon!")
            else:
                log.error(f"Error: Channel with ID {NCO_COMMS} not found in Main Guild.")
        else:
            log.error(f"Error: Guild with ID {GUILD_ID} not found.")
        
        if spd_guild:
            engine_room_channel = spd_guild.get_channel(ENGINE_ROOM)
            if engine_room_channel:
                await engine_room_channel.send("I'm going on LOA, be back soon!")
            else:
                log.error(f"Error: Channel with ID {ENGINE_ROOM} not found in SPD Guild.")
        else:
            log.error(f"Error: Guild with ID {SPD_ID} not found.")

async def setup(bot: commands.Bot):
    await bot.add_cog(BotDown(bot))