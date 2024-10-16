import discord
import logging
from discord.ext import commands, tasks
from config import ENGINE_ROOM, SPD_ID, BOT_STATUS, GUILD_ID, NSC_ROLES
from datetime import datetime, timedelta
from io import BytesIO

log = logging.getLogger(__name__)

class BotStatus(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.status_embed = None
        #self.update_status_embed.start()

    def cog_unload(self):
        self.update_status_embed.cancel()

    @commands.command(name="botstatus")
    @commands.has_any_role(*NSC_ROLES)
    async def set_status(self, ctx, status: int):
        """
        Sets the bot's LOA status and updates the status embed.

        Args:
            status: 1 for online, 0 for offline.
        """
        if status not in [0, 1]:
            await ctx.send("Invalid status. Use 1 for online, 0 for offline.")
            return
        
        if status == 0:
            spd_guild = self.bot.get_guild(SPD_ID)
            if spd_guild:
                engine_room_channel = spd_guild.get_channel(ENGINE_ROOM)
                if engine_room_channel:
                    await engine_room_channel.send("I'm going on LOA, be back soon!")
                else:
                    print(f"Error: Channel with ID {ENGINE_ROOM} not found in SPD Guild.")
            else:
                print(f"Error: Guild with ID {SPD_ID} not found.")

        guild = self.bot.get_guild(GUILD_ID)
        try:
            channel = guild.get_channel(BOT_STATUS)
            print(channel)
        except discord.NotFound as e:
            log.error("Channel not found: {e}")
            return
        
        if not self.status_embed:
                     
            # Create the embed if it doesn't exist
            self.status_embed = discord.Embed(
                title="Paul's LOA Status",
                description="Hi, I'm Paul! My services are up and running!" if status == 1 else "I'm on LOA, be back when they're done with me.",
                color=discord.Color.red() if status == 0 else discord.Color.green(),
            )
            self.status_embed.set_footer(text="If you see any issues, please contact the NSC Department through a ticket and let us know what you see!")
            status_message = await channel.send(embed=self.status_embed)
            self.loa_message_id = status_message.id

            # Set thumbnail for initial embed creation
            if status == 0:
                with open("src/assets/paul_offline.png", "rb") as f:  # Read image from src/assets
                    thumbnail = BytesIO(f.read())
                    await status_message.add_files(discord.File(thumbnail, filename="paul_offline.png"))
                    self.status_embed.set_thumbnail(url=f"attachment://paul_offline.png")
            else:
                with open("src/assets/paul_online.png", "rb") as f:  # Read image from src/assets
                    thumbnail = BytesIO(f.read())
                    await status_message.add_files(discord.File(thumbnail, filename="paul_online.png"))
                    self.status_embed.set_thumbnail(url=f"attachment://paul_online.png")

            await status_message.edit(embed=self.status_embed)  # Update the embed with the thumbnail

        else:
            # Update the existing embed
            self.status_embed.description = "Hi, I'm Paul! My services are up and running!" if status == 1 else "I'm on LOA, be back when they're done with me."
            self.status_embed.color = discord.Color.red() if status == 0 else discord.Color.green()
            self.status_embed.timestamp = datetime.now() + timedelta(hours=12)

            # Update the thumbnail
            status_message = await channel.fetch_message(self.loa_message_id)
            if status == 0:
                with open("src/assets/paul_offline.png", "rb") as f:  # Read image from src/assets
                    thumbnail = BytesIO(f.read())
                    await status_message.add_files(discord.File(thumbnail, filename="paul_offline.png"))
                    self.status_embed.set_thumbnail(url=f"attachment://paul_offline.png")
            else:
                with open("src/assets/paul_online.png", "rb") as f:  # Read image from src/assets
                    thumbnail = BytesIO(f.read())
                    await status_message.add_files(discord.File(thumbnail, filename="paul_online.png"))
                    self.status_embed.set_thumbnail(url=f"attachment://paul_online.png")

            await status_message.edit(embed=self.status_embed)

        await ctx.send("LOA status updated!")

    @tasks.loop(minutes=1)
    async def update_status_embed(self):
        """Periodically updates the status embed's timestamp."""
        guild = self.bot.get_guild(GUILD_ID)
        channel = guild.get_channel(BOT_STATUS)
        try:
            status_message = await channel.fetch_message(self.loa_message_id)
            if self.status_embed:
                self.status_embed.timestamp = datetime.now() + timedelta(hours=12)
                await status_message.edit(embed=self.status_embed)
        except discord.NotFound:
            print("Error: Status message not found.")

async def setup(bot: commands.Bot):
    await bot.add_cog(BotStatus(bot))