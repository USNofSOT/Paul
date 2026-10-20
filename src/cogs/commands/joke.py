import logging

import requests
from discord.ext import commands

log = logging.getLogger(__name__)
REQUEST_TIMEOUT_SECONDS = 10


class Jokes(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.command()
    async def joke(self, ctx):
        """Tells a random joke."""
        try:
            url = "https://icanhazdadjoke.com/"
            headers = {"Accept": "application/json"}
            response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            joke = data["joke"]
            await ctx.send(joke)
        except requests.exceptions.RequestException:
            log.warning("Dad joke request failed", exc_info=True)
            await ctx.send("Oops, something went wrong while fetching a joke. Please try again later.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Jokes(bot))  # Classname(bot)
