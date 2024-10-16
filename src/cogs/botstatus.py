import discord
import logging
from discord.ext import commands, tasks
from config import BOT_STATUS, GUILD_ID, NSC_ROLES
from datetime import datetime, timedelta
import json
import os

log=logging.getLogger(__name__)
ENV : str = os.getenv('ENVIRONMENT', "DEV")

class BotStatus(commands.Cog):
      
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.status_embed = None
        self.load_status_message_id()  # Load the message ID on startup
        

    def cog_unload(self):
        self.update_status_embed.cancel()

    def load_status_message_id(self):
        """Loads the status message ID from the file."""
        if not ENV=="PROD":
            log.info("Not In Production")
            return
        try:
            with open("status_message_id.json", "r") as f:
                data = json.load(f)
                self.status_message_id = data.get("message_id")
        except FileNotFoundError:
            self.status_message_id = None

    def save_status_message_id(self):
        """Saves the status message ID to the file."""
        with open("status_message_id.json", "w") as f:
            json.dump({"message_id": self.status_message_id}, f)

    @commands.command(name="botstatus")
    @commands.has_any_role(*NSC_ROLES)
    async def set_status(self, ctx, status: int):
        """
        Sets the bot's LOA status and updates the status embed.

        Args:
            status: 1 for online, 0 for offline.
        """
        if not ENV=="PROD":
            log.info("Not In Production")
            return
        if status not in [0, 1]:
            await ctx.send("Invalid status. Use 1 for online, 0 for offline.")
            return

        if status == 0:
            # Set bot's profile picture to the "down" image
            with open("src/assets/paul_offline.png", "rb") as f:
                await self.bot.user.edit(avatar=f.read())
        else:
            # Set bot's profile picture back to the original
            with open("src/assets/paul_online.png", "rb") as f:
                await self.bot.user.edit(avatar=f.read())

        guild = self.bot.get_guild(GUILD_ID)
        channel = guild.get_channel(BOT_STATUS)

        if not self.status_message_id:
            # Create the embed and send it
            embed = discord.Embed(
                title="Paul's LOA Status",
                description="Hi, I'm Paul! My services are up and running!" if status == 1 else "I'm on LOA, be back when they're done with me.",
                color=discord.Color.green() if status == 1 else discord.Color.red(), timestamp=datetime.now(),
            )
            embed.set_thumbnail(url=self.bot.user.avatar.url)
            embed.add_field(name="Support", value="If you see any issues, please contact the [NSC Department through a ticket](https://discord.com/channels/971718695602778162/1123675218884436119/1292309423250870314) and let us know what you see!")
            message = await channel.send(embed=embed)
            self.status_message_id = message.id
            self.save_status_message_id()  # Save the message ID
        else:
            # Fetch the existing embed and update it
            try:
                message = await channel.fetch_message(self.status_message_id)
                embed = message.embeds[0]
                embed.set_thumbnail(url=self.bot.user.avatar.url)
                embed.description = "Hi, I'm Paul! My services are up and running!" if status == 1 else "I'm on LOA, be back when they're done with me."
                embed.set_field_at(index=0,name="Support", value="If you see any issues, please contact the [NSC Department through a ticket](https://discord.com/channels/971718695602778162/1123675218884436119/1292309423250870314) and let us know what you see!")
                embed.color = discord.Color.green() if status == 1 else discord.Color.red()
                embed.timestamp = datetime.now()
                await message.edit(embed=embed)
            except discord.NotFound:
                log.error("Error: Status message not found.")

        await ctx.send("LOA status updated!")
        
    

async def setup(bot: commands.Bot):
    await bot.add_cog(BotStatus(bot))