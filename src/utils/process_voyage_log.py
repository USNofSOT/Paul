from src.data.repository.hosted_repository import check_hosted_log_id_exists, save_hosted_data
from src.data.repository.sailor_repository import update_or_create_sailor_by_discord_id, \
    increment_voyage_count_by_discord_id
from src.data.repository.voyage_repository import batch_save_voyage_data, check_voyage_log_id_with_target_id_exists


class Process_Voyage_Log:
    #subroutine to check if a voyage log already exists, and processes it if it does not.
    async def process_voyage_log(message):
        log_id = message.id
        host_id = message.author.id
        log_time = message.created_at
        participant_ids = []
        for user in message.mentions:
            participant_ids.append(user.id)

        #print(f" logid: {log_id} hostid: {host_id} time: {log_time}") # Used to view data on console as it is processed.

        # 1. Check if the log has already been processed
        if check_hosted_log_id_exists(log_id):
            return  # Skip if the log has already been processed

        # 2. If not, process the log. But first, ensure the host is in the Sailor table
        update_or_create_sailor_by_discord_id(host_id)
        save_hosted_data(log_id, host_id, log_time)
        # 3.Log Voyage Count

        voyage_data = []
        for participant_id in participant_ids:
            if not check_voyage_log_id_with_target_id_exists(log_id, participant_id):
                    # Ensure the participant is in the Sailor table
                    update_or_create_sailor_by_discord_id(participant_id)
                    # Add the voyage data to the list
                    voyage_data.append((log_id, participant_id, log_time))
                    # Increment the voyage count for the participant
                    increment_voyage_count_by_discord_id(participant_id)

        # Batch insert voyage data
        batch_save_voyage_data(voyage_data)