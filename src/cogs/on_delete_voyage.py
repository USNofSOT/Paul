import discord
from discord.ext import commands
from discord import app_commands

from src.config import VOYAGE_LOGS
from src.data.repository.hosted_repository import remove_hosted_entry_by_log_id
from src.data.repository.sailor_repository import decrement_voyage_count_by_discord_id, \
    decrement_hosted_count_by_discord_id
from src.data.repository.voyage_repository import remove_voyage_log_entry, remove_voyage_log_entries

class On_Delete_Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id == VOYAGE_LOGS:
                log_id = message.id
                host_id = message.author.id
                participant_ids = [user.id for user in message.mentions]

                # Decrement hosted count
                decrement_hosted_count_by_discord_id(host_id)
                remove_hosted_entry_by_log_id(log_id)

                # Decrement voyage counts for participants
                for participant_id in participant_ids:
                    decrement_voyage_count_by_discord_id(participant_id)
                    print(f"Voyage count deleted: {participant_id}")
                # Remove entries from VoyageLog table (if necessary)
                remove_voyage_log_entries(log_id)
                print(f"Voyage log deleted: {log_id}")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(On_Delete_Voyages(bot))  # Classname(bot)