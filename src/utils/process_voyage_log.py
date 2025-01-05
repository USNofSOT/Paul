import re
from logging import getLogger

import discord

from src.data.repository.hosted_repository import HostedRepository
from src.data.repository.sailor_repository import SailorRepository
from src.data.repository.voyage_repository import VoyageRepository
from src.utils.ship_utils import (
    get_auxiliary_ship_from_content,
    get_count_from_content,
    get_main_ship_from_content,
    get_ship_role_id_by_member,
)

log = getLogger(__name__)

def get_gold_count_from_content(content: str) -> int:
    """
    Get the gold count from the content.

    The gold count will always include the word "gold" or the gold emoji. Either in the beginning or the end of the content.
    The gold count will be a number with or without commas and periods or spaces.
    """
    pattern = r"(?i)(?:gold[:> a-z]{0,25}\s*(\d[\d\s]*)|(\d[\d\s]*)\s*[:< a-z]gold)"
    text_without_ids = re.sub(r':\d+>', '>', content.replace(",", "").replace(".", "").replace("<", ""))
    match = re.search(pattern, text_without_ids)
    if match:
        return min(int((match.group(1) or match.group(2)).replace(" ", "")), 20000000)
    return 0

def get_doubloon_count_from_content(content: str) -> int:
    pattern = r"(?i)(?:doubloon[s]?[:> a-z]*\s*(\d+)|^(?!.*\d\n)(\d+)\s*[:< a-z]doubloon[s]?)"
    text_without_ids = re.sub(r':\d+>', '>', content.replace(",", "").replace(".", "").replace("<", ""))
    match = re.search(pattern, text_without_ids)
    return min(int(match.group(1) or match.group(2)), 20000000) if match else 0

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
        log.info(f"[{log_id}] Voyage log message received:")
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
        hosted_repository.save_hosted_data(
            log_id,
            host_id,
            log_time,
            get_ship_role_id_by_member(message.author),
            ship_name=get_main_ship_from_content(message.content),
            auxiliary_ship_name=get_auxiliary_ship_from_content(message.content),
            ship_voyage_count=get_count_from_content(message.content),
            gold_count=get_gold_count_from_content(message.content),
            doubloon_count=get_doubloon_count_from_content(message.content)
        )
        # 3.Log Voyage Count

        voyage_data = []
        for participant_id in participant_ids:
            if not voyage_repository.check_voyage_log_id_with_target_id_exists(log_id, participant_id):
                    # Ensure the participant is in the Sailor table
                    sailor_repository.update_or_create_sailor_by_discord_id(participant_id)
                    # Add the voyage data to the list
                    voyage_data.append((log_id, participant_id, log_time, get_ship_role_id_by_member(message.guild.get_member(participant_id))))
                    # Increment the voyage count for the participant
                    sailor_repository.increment_voyage_count_by_discord_id(participant_id)

        # Batch insert voyage data
        voyage_repository.batch_save_voyage_data(voyage_data)
