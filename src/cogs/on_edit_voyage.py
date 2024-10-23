from logging import getLogger

import discord
from discord.ext import commands
from discord import app_commands
from discord import RawMessageUpdateEvent

from src.config import VOYAGE_LOGS, GUILD_ID
from src.data.repository.hosted_repository import remove_hosted_entry_by_log_id, HostedRepository
from src.data.repository.sailor_repository import decrement_voyage_count_by_discord_id, \
    decrement_hosted_count_by_discord_id
from src.data.repository.voyage_repository import remove_voyage_log_entries, VoyageRepository
from src.data.repository.subclass_repository import SubclassRepository
from utils.process_voyage_log import Process_Voyage_Log

#On Message Editing events adjust voyages

log = getLogger(__name__)

class On_Edit_Voyages(commands.Cog):
    # ... your existing code ...

    def __init__(self, bot: commands.Bot) -> None:
            self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        self.subclass_repository = SubclassRepository()
        self.hosted_repository = HostedRepository()
        self.voyage_repository = VoyageRepository()
        if payload.channel_id == VOYAGE_LOGS:
            log.info(f"[{payload.message_id}] [ON_EDIT] Voyage log message edited.")
            log_id = payload.message_id
            try:
                host = self.hosted_repository.get_host_by_log_id(log_id)
                if host:
                    host_id = host.discord_id

                else:
                    log.info(f"[{log_id}] Voyage:{log_id} was not logged before.")
                    return
                
                participant_ids = [user.discord_id for  user in self.voyage_repository.get_sailors_by_log_id(log_id)]
                
                log.info(f"[{log_id}] Message deleted in voyage log channel.")

                # Decrement hosted count
                decrement_hosted_count_by_discord_id(host_id)
                remove_hosted_entry_by_log_id(log_id)
                log.info(f"[{log_id}] Removed hosted entry for: {host_id}")

                # Decrement voyage counts for participants
                for participant_id in participant_ids:
                    decrement_voyage_count_by_discord_id(participant_id)
                    log.info(f"[{log_id}] Voyage log entry removed for participant: {participant_id}")

                # Remove entries from VoyageLog table (if necessary)
                remove_voyage_log_entries(log_id)
                log.info(f"[{log_id}] Voyage log entries removed.")
            
                guild = self.bot.get_guild(GUILD_ID)
                logs_channel = guild.get_channel(VOYAGE_LOGS)
                log_message = await logs_channel.fetch_message(int(log_id))

                await Process_Voyage_Log.process_voyage_log(log_message)
                
            except AttributeError as e:
                log.info(f"[{log_id}] Was never in Database to edit.")
                log.warning(f"[{log_id}], {e}")
            except Exception as e:
                log.error(e)
                raise e
                
            
        self.subclass_repository.close_session()
        self.hosted_repository.close_session()
        self.voyage_repository.close_session()

async def setup(bot: commands.Bot):
    await bot.add_cog(On_Edit_Voyages(bot))  # Classname(bot)