import re
from datetime import UTC, datetime
from logging import getLogger

import discord
from utils.ship_utils import get_voyage_type_from_content

from src.config.main_server import GUILD_ID, VOYAGE_PLANNING
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

LOG_KEYWORD_SYNONYM = {
    "doubloon": "doubloons",
    "fish": "fishes",
    "ancient coin": "ancient coins",
    "AncientCoin" : "ancient coins",
    "AncientCoins" : "ancient coins",
    "🐟": "fishes",
}

def get_count_from_content_by_keyword(content: str, keywords: str) -> int:
    """
    Get the count from the content based on the keyword.

    The count will always include the keyword or its emoji. Either in the beginning or the end of the content.
    The count will be a number with or without commas and periods or spaces.

    Args:
        content (str): The content to search for the count.
        keywords (str): The keyword to search for. Can be either 'gold', 'doubloons', 'fishes', 'ancient coins'
    """

    pattern = "(?im)(?:" + keywords + r"[-:> a-z]{0,25}\s*(\d[\d\s]*))"
    # 1. Replace aliases with the keyword
    for synonym, keyword in LOG_KEYWORD_SYNONYM.items():
        content = content.lower().replace(synonym.lower(), keyword.lower())
    # 2. Remove markdown
    content = content.replace("*", "").replace("_", "").replace("`", "")
    # 3. Remove commas and periods
    content = content.replace(",", "").replace(".", "")
    # 4. Remove discord embedded id's
    content = re.sub(r"\d+>|<|>", "", content.replace(":", ""))

    matches = re.findall(pattern, content)

    if matches:
        highest = 0
        for match in matches:
            try:
                count = int(match.replace(" ", ""))
                if count > highest:
                    highest = count
            except ValueError:
                continue
        return min(highest, 20000000)
    else:
        return 0

def get_gold_count_from_content(content: str) -> int:
    return get_count_from_content_by_keyword(content, "gold")

def get_doubloon_count_from_content(content: str) -> int:
    return get_count_from_content_by_keyword(content, "doubloons")

def get_fish_count_from_content(content: str) -> int:
    return get_count_from_content_by_keyword(content, "fishes")

def get_ancient_coin_count_from_content(content: str) -> int:
    return get_count_from_content_by_keyword(content, "ancient coins")


def get_voyage_planning_message_id_from_content(content) -> int | None:
    pattern = rf"discord\.com/channels/{GUILD_ID}/{VOYAGE_PLANNING}/(\d+)$"

    matches = re.findall(pattern, content)
    if matches:
        return matches[0]
    return None

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

        vp_id = None
        if message.created_at >= datetime(2026, 1, 15, tzinfo=UTC):
            vp_id = get_voyage_planning_message_id_from_content(message.content)

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
            doubloon_count=get_doubloon_count_from_content(message.content),
            fish_count=get_fish_count_from_content(message.content),
            ancient_coin_count=get_ancient_coin_count_from_content(message.content),
            voyage_type=get_voyage_type_from_content(message.content),
            voyage_planning_message_id=vp_id
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
