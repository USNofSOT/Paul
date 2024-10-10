import config
from utils.database_manager import DatabaseManager

class Process_Voyage_Log:
    #subroutine to check if a voyage log already exists, and processes it if it does not.
    async def process_voyage_log(message):
        db_manager = DatabaseManager()
        log_id = message.id
        host_id = message.author.id
        log_time = message.created_at
        participant_ids = []
        for user in message.mentions:
            participant_ids.append(user.id)

        #print(f" logid: {log_id} hostid: {host_id} time: {log_time}") # Used to view data on console as it is processed.

        # 1. Check if the log_id already exists in the database
        if db_manager.hosted_log_id_exists(log_id):
            return  # Skip if the log has already been processed

        # 2. If not, process the log as you did in on_message
        db_manager.log_hosted_data(log_id, host_id, log_time)
        # 3.Log Voyage Count

        voyage_data = []
        for participant_id in participant_ids:
            if not db_manager.voyage_log_entry_exists(log_id, participant_id):
                    voyage_data.append((log_id, participant_id, log_time))
                    db_manager.increment_voyage_count(participant_id)

        # Batch insert voyage data
        db_manager.batch_log_voyage_data(voyage_data)