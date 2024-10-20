import requests
from discord.ext import commands


class Jokes(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    @commands.command()
    async def joke(self, ctx):
        """Tells a random joke."""
        try:
            url = "https://icanhazdadjoke.com/"
            headers = {"Accept": "application/json"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            data = response.json()
            joke = data["joke"]
            await ctx.send(joke)
        except requests.exceptions.RequestException as e:
            await ctx.send(f"Oops, something went wrong: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Jokes(bot))  # Classname(bot)