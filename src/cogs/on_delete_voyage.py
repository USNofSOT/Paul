import discord, config
from discord.ext import commands
from discord import app_commands
from config import VOYAGE_LOGS
from utils.database_manager import DatabaseManager

# Remove voyages, and hosted on message deletion

db_manager = DatabaseManager()

class On_Delete_Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message_delete(message):
        if message.channel.id == VOYAGE_LOGS:
                log_id = message.id
                host_id = message.author.id
                participant_ids = [user.id for user in message.mentions]

                # Decrement hosted count
                db_manager.decrement_count(host_id, "hosted_count")
                db_manager.remove_hosted_entry( log_id)

                # Decrement voyage counts for participants
                for participant_id in participant_ids:
                    db_manager.decrement_count(participant_id, "voyage_count")
                    print(f"Voyage count deleted: {participant_id}")
                # Remove entries from VoyageLog table (if necessary)
                db_manager.remove_voyage_log_entries(log_id)
                print(f"Voyage log deleted: {log_id}")
        

async def setup(bot: commands.Bot):
    await bot.add_cog(On_Delete_Voyages(bot))  # Classname(bot)