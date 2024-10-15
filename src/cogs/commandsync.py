from discord.ext import commands
from config import NSC_ROLE

class CommandSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commandsync")
    @commands.has_any_role(NSC_ROLE)
    async def commandsync(self, ctx):
        """Syncs the application commands."""
        await self.bot.tree.sync()
        await ctx.send("Application commands synced!")

async def setup(bot):
    await bot.add_cog(CommandSync(bot))