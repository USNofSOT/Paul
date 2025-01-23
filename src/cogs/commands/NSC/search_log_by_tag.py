import datetime

import discord
from config import GUILD_ID, NSC_ROLES, VOYAGE_LOGS
from discord.ext import commands
from utils.process_voyage_log import get_count_from_content_by_keyword


class SearchLogByTag(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    @commands.has_any_role(*NSC_ROLES)
    async def search_log_by_tag(self, context: commands.Context, tag: str, value: str = None):
        if not tag:
            await context.send("Please provide a tag to search for.")
            return
        if not value:
            await context.send("Please provide a value to search for.")
            return

        channel = self.bot.get_guild(GUILD_ID).get_channel(VOYAGE_LOGS)

        thirty_days_ago = datetime.datetime.now() - datetime.timedelta(days=60)

        embed = discord.Embed(title="Search Results", color=0x00ff00)

        embed.add_field(name="Tag", value=tag, inline=True)
        embed.add_field(name="Value", value=value, inline=True)

        try:
            async for message in channel.history(oldest_first=False, after=thirty_days_ago, limit=None):
                content = message.content
                if tag in content:
                    count = get_count_from_content_by_keyword(content, value)
                    embed.add_field(name=f"Voyage ID: https://discord.com/channels/{GUILD_ID}/{VOYAGE_LOGS}/{message.id}",
                                    value=f"- Host: {message.author.mention}\n- Count: {count}",
                                    inline=False)

            await context.send(embed=embed)
        except Exception as e:
            await context.send(f"An error occurred: {e}")

    @search_log_by_tag.error
    async def search_log_by_tag_error(self, context: commands.Context, error: commands.CommandError):
        if isinstance(error, commands.MissingAnyRole):
            await context.send("You do not have the required role to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await context.send("Please provide a tag and value to search for. `!search_log_by_tag <tag> <value>`")
        else:
            await context.send(f"An error occurred: {error}")


async def setup(bot: commands.Bot):
    await bot.add_cog(SearchLogByTag(bot))  # Classname(bot)
