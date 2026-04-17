from discord.ext import commands

from src.security import require_any_role, audit_interaction, Role


class CommandSync(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="commandsync")
    @require_any_role(Role.NSC_OPERATOR)
    @audit_interaction
    async def commandsync(self, ctx):
        """Syncs the application commands."""
        await self.bot.tree.sync()
        await ctx.send("Application commands synced!")

async def setup(bot):
    await bot.add_cog(CommandSync(bot))