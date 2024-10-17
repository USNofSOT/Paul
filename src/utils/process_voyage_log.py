from logging import getLogger

import discord

from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository

log = getLogger(__name__)

class Process_Voyage_Log:
    #subroutine to check if a voyage log already exists, and processes it if it does not.
    async def process_voyage_log(
            message: discord.Message,
            voyage_repository: VoyageRepository = VoyageRepository(),
            hosted_repository: HostedRepository = HostedRepository(),
            sailor_repository: SailorRepository = SailorRepository()
    ):
        log_id = message.id
        host_id = message.author.id
        log_time = message.created_at
        participant_ids = []
        log.info(f"[{log_id}] [PROCESS] Voyage log message received.")
        for user in message.mentions:
            participant_ids.append(user.id)

        if len(participant_ids) <= 1:
            log.info(f"[{log_id}] Not enough participants found in voyage log. Skipping.")
            return # Skip if there are no participants

        log.info(f"[{log_id}] Processing voyage log for host: {host_id} with {len(participant_ids)} participants.")

        # 1. Check if the log has already been processed
        if hosted_repository.check_hosted_log_id_exists(log_id):
            log.debug(f"[{log_id}] Voyage log has already been processed. Skipping.")
            return  # Skip if the log has already been processed

        # 2. If not, process the log. But first, ensure the host is in the Sailor table
        sailor_repository.update_or_create_sailor_by_discord_id(host_id)
        hosted_repository.save_hosted_data(log_id, host_id, log_time)
        # 3.Log Voyage Count

        voyage_data = []
        for participant_id in participant_ids:
            if not voyage_repository.check_voyage_log_id_with_target_id_exists(log_id, participant_id):
                    # Ensure the participant is in the Sailor table
                    sailor_repository.update_or_create_sailor_by_discord_id(participant_id)
                    # Add the voyage data to the list
                    voyage_data.append((log_id, participant_id, log_time))
                    # Increment the voyage count for the participant
                    sailor_repository.increment_voyage_count_by_discord_id(participant_id)

        # Batch insert voyage data
        voyage_repository.batch_save_voyage_data(voyage_data)