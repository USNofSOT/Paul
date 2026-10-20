from logging import getLogger

from discord.ext import commands

from src.security import require_any_role, audit_interaction, Role
from src.utils.populater import Populater

log = getLogger(__name__)

class PopulateVoyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="populate_voyages")
    @require_any_role(Role.NSC_ADMINISTRATOR)
    @audit_interaction
    async def populate_voyages(self, ctx, arg: int = 1):
        if arg == -1:
            max_voyages = None
        else:
            max_voyages = arg
        log.info(f"Populating voyages with a limit of {max_voyages}")
        await ctx.send("Attempting to populate voyages.")
        await Populater(self.bot).synchronize(limit=max_voyages)
        await ctx.send("Voyages populated.")


async def setup(bot: commands.Bot):
    await bot.add_cog(PopulateVoyages(bot))
