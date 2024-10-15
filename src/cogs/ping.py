import discord, config
from discord.ext import commands
from discord import app_commands
# from utils.database_manager import DatabaseManager   # Imports Database Manager from Utilies if needed uncomment it!

class Ping(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    
    @commands.command()
    async def ping(self,ctx):
        # Get the appropriate avatar URL
        avatar_url = ctx.author.guild_avatar.url if ctx.author.guild_avatar else ctx.author.avatar.url
        ping_embed = discord.Embed(title="Ping", description="Pong!", color=discord.Color.blue())
        ping_embed.add_field(name=f"{self.bot.user.name}'s Latency (ms)", value=f"{round(self.bot.latency * 1000)}", inline=False)
        ping_embed.set_footer(text=f"Pinged by {ctx.author.name}", icon_url=avatar_url)
        await ctx.send(embed=ping_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Ping(bot))  # Classname(bot)
        