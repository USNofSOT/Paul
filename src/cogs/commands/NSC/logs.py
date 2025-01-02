from logging import getLogger

import discord
from discord.ext import commands

from src.config import NSC_ROLES
from src.utils.logger import get_most_recent_log_file, get_most_recent_error_log_file

log = getLogger(__name__)

class Logs(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command(name="logs")
    @commands.has_any_role(*NSC_ROLES)
    async def populate_voyages(self, ctx):
        log_file = get_most_recent_log_file()
        error_log_file = get_most_recent_error_log_file()

        channel = ctx.channel

        log.warning(f"Sending log files to {channel}")

        try:
            if error_log_file:
                await channel.send(file=discord.File(error_log_file))
            else:
                await channel.send("No error log files found.")
            if log_file:
                await channel.send(file=discord.File(log_file))
            else:
                await channel.send("No log files found.")
        except Exception as e:
            log.error(f"Error sending log files: {e}")




async def setup(bot: commands.Bot):
    await bot.add_cog(Logs(bot))
