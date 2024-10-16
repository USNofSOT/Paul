import discord
import logging
from discord.ext import commands
from src.config import NCO_COMMS, ENGINE_ROOM, GUILD_ID, SPD_ID, NSC_ROLES

log = logging.getLogger(__name__)

class BotUp(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="botup")
    @commands.has_any_role(NSC_ROLES)
    async def botdown(self, ctx):
        """Sends an LOA notification to the specified channels."""
        main_guild = GUILD_ID
        spd_guild = SPD_ID
        
        if main_guild:
            nco_coms_channel = main_guild.get_channel(NCO_COMMS)
            if nco_coms_channel:
                await nco_coms_channel.send("I'm Back from LOA")
            else:
                log.error(f"Error: Channel with ID {NCO_COMMS} not found in Main Guild.")
        else:
            log.error(f"Error: Guild with ID {GUILD_ID} not found.")

async def setup(bot: commands.Bot):
    await bot.add_cog(BotUp(bot))