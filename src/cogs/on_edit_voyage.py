from logging import getLogger

import discord
from discord.ext import commands
from discord import app_commands

from src.config import VOYAGE_LOGS
from src.data.repository.sailor_repository import decrement_voyage_count_by_discord_id
from src.data.repository.voyage_repository import remove_voyage_by_log_id, remove_voyage_log_entry, \
    check_voyage_log_id_with_target_id_exists, save_voyage

#On Message Editing events adjust voyages

log = getLogger(__name__)

class On_Edit_Voyages(commands.Cog):
    # ... your existing code ...

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.channel_id == int(VOYAGE_LOGS):
            log_id = payload.message_id
            
            # Try to get the messages from the cache
            before = self.bot.get_message(log_id)
            
            # If the message is not in the cache, fetch it
            if before is None:
                channel = self.bot.get_channel(payload.channel_id)
                before = await channel.fetch_message(log_id)
            
            after = await channel.fetch_message(log_id)

            if not before.author.bot:
                log.info(f"[{before.id}] Message edited in voyage log channel.")
                old_participant_ids = [user.id for user in before.mentions]
                new_participant_ids = [user.id for user in after.mentions]

                # Participants removed from the log
                removed_participants = set(old_participant_ids) - set(new_participant_ids)
                for participant_id in removed_participants:
                    # Decrement voyage count for the participant
                    decrement_voyage_count_by_discord_id(participant_id)
                    # Remove entry from VoyageLog table
                    remove_voyage_log_entry(after.id, participant_id)
                    log.info(f"[{before.id}] Voyage log entry removed for participant: {participant_id}")

                # New participants added to the log
                added_participants = set(new_participant_ids) - set(old_participant_ids)
                for participant_id in added_participants:
                    # Add new entry to VoyageLog table if needed
                    if not check_voyage_log_id_with_target_id_exists(after.id, participant_id):
                        # This will both save the voyage log entry and increment the voyage count for the participant
                        save_voyage(after.id, participant_id, after.created_at)
                        log.info(f"[{before.id}] Voyage log entry added for participant: {participant_id}")

async def setup(bot: commands.Bot):
    await bot.add_cog(On_Edit_Voyages(bot))  # Classname(bot)