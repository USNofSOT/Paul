from logging import getLogger

from discord.ext import commands

from src.config import VOYAGE_LOGS
from src.data.repository.hosted_repository import remove_hosted_entry_by_log_id
from src.data.repository.sailor_repository import decrement_voyage_count_by_discord_id, \
    decrement_hosted_count_by_discord_id
from src.data.repository.subclass_repository import SubclassRepository
from src.data.repository.voyage_repository import remove_voyage_log_entries

log = getLogger(__name__)

class On_Delete_Voyages(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.channel.id == VOYAGE_LOGS and not message.author.bot:
                subclass_repository: SubclassRepository = SubclassRepository()

                log_id = message.id
                host_id = message.author.id
                participant_ids = [user.id for user in message.mentions]

                log.info(f"[{log_id}] Message deleted in voyage log channel.")

                # Decrement hosted count
                decrement_hosted_count_by_discord_id(host_id)
                remove_hosted_entry_by_log_id(log_id)
                log.info(f"[{log_id}] Removed hosted entry for: {host_id}")

                # Remove subclass entries
                subclass_entries = subclass_repository.delete_all_subclass_entries_for_log_id(log_id)

                # Decrement voyage counts for participants
                for participant_id in participant_ids:
                    decrement_voyage_count_by_discord_id(participant_id)
                    log.info(f"[{log_id}] Voyage log entry removed for participant: {participant_id}")
                # Remove entries from VoyageLog table (if necessary)
                remove_voyage_log_entries(log_id)
                log.info(f"[{log_id}] Voyage log entries removed.")


async def setup(bot: commands.Bot):
    await bot.add_cog(On_Delete_Voyages(bot))  # Classname(bot)