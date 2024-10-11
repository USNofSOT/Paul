import discord, config
from discord.ext import commands
from discord import app_commands
from config import VOYAGE_LOGS
from utils.database_manager import DatabaseManager

#On Message Editing events adjust voyages

db_manager = DatabaseManager()

class On_Edit_Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.channel.id == int(VOYAGE_LOGS):
            print(f"Edit Seen: {before.id}")
            old_participant_ids = [user.id for user in before.mentions]
            new_participant_ids = [user.id for user in after.mentions]

            # Participants removed from the log
            removed_participants = set(old_participant_ids) - set(new_participant_ids)
            for participant_id in removed_participants:
                db_manager.decrement_count(participant_id, "voyage_count")
                db_manager.remove_voyage_log_entry(after.id, participant_id)
                print(f"Voyage log removed: {after.id}")

            # New participants added to the log
            added_participants = set(new_participant_ids) - set(old_participant_ids)
            for participant_id in added_participants:
                db_manager.increment_voyage_count(participant_id)
                # Add new entry to VoyageLog table if needed
                if not db_manager.voyage_log_entry_exists(after.id, participant_id):
                    db_manager.log_voyage_data(after.id, participant_id, after.created_at)
                    print(f"Voyage log added: {after.id}")

async def setup(bot: commands.Bot):
    await bot.add_cog(On_Edit_Voyages(bot))  # Classname(bot)