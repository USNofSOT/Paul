import logging

from src.data.repository.hosted_repository import remove_hosted_entry_by_log_id
from src.data.repository.sailor_repository import decrement_voyage_count_by_discord_id, \
    decrement_hosted_count_by_discord_id
from src.data.repository.voyage_repository import remove_voyage_log_entries
from src.utils.discord_utils import alert_engineers

log = logging.getLogger(__name__)

async def remove_voyage_log_data(bot, log_id, hosted_repository, voyage_repository, subclass_repository = None):
    log_txt = f"[{log_id}] remove_voyage_log_data called. \n"
    try:
        host = hosted_repository.get_host_by_log_id(log_id)
        if host:
            log.info(f"[{log_id}] Voyage log message has a hosted entry, removing old data.")
            host_id = host.target_id
            participant_ids = [user.discord_id for user in voyage_repository.get_sailors_by_log_id(log_id)]

            for participant_id in participant_ids:
                log_txt += f" Removing voyage count for {participant_id}. \n"
                decrement_voyage_count_by_discord_id(participant_id)
                log_txt += f" Removed voyage count for {participant_id}. \n"
                if subclass_repository:
                    log_txt += f" Removing subclass entries for {participant_id}. \n"
                    subclass_repository.delete_subclasses_for_target_in_log(participant_id, log_id)
                    log_txt += f" Removed subclass entries for {participant_id}. \n"

            log_txt += f" Removing voyage log entries for {log_id}. \n"
            remove_voyage_log_entries(log_id)
            log_txt += f" Removed voyage log entries for {log_id}. \n"
            log_txt += f" Removing hosted count for {host_id}. \n"
            decrement_hosted_count_by_discord_id(host_id)
            log_txt += f" Removed hosted count for {host_id}. \n"
            log_txt += f" Removing hosted entry for {log_id}. \n"
            remove_hosted_entry_by_log_id(log_id)
            log_txt += f" Removed hosted entry for {log_id}. \n"

            log.info(f"[{log_id}] Voyage log data successfully removed.")
    except Exception as e:
        log.error(f"[{log_id}] Error removing old data: {e}")
        await alert_engineers(
            bot=bot,
            message=f"Error removing data from voyage log message {log_id} \n {log_txt}",
            exception=e
        )