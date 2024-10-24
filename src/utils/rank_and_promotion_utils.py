import logging

import discord

from src.config.ranks import RANKS
from src.data.structs import NavyRank, Award

log = logging.getLogger(__name__)

def has_award_or_higher(
    target: discord.Member,
    required_award: Award,
    category_awards: [Award]
) -> bool:
    """
    Check if the target has the required award or higher.
    """
    member_role_ids = [role.id for role in target.roles]
    member_awards = [award for award in category_awards if award.role_id in member_role_ids]
    required_threshold = required_award.threshold
    log.info(f"Checking if {target.display_name} has the required award or higher: {required_award}")
    for award in member_awards:
        if award.threshold >= required_threshold:
            log.info(f"{target.display_name} has the required award or higher: {award} - {award.threshold} >= {required_threshold}")
            return True

def get_current_rank(
        target: discord.Member
) -> NavyRank:
    """
    Given the current member, return the rank with the highest index that the member has.
    """
    highest_rank = None
    for rank in RANKS:
        if any(role.id in rank.role_ids for role in target.roles):
            if highest_rank is None or rank.index < highest_rank.index:
                highest_rank = rank
    return highest_rank

def get_rank_by_index(
        index: int
) -> NavyRank:
    """
    Given a given index, return the corresponding NavyRank object
    """
    for rank in RANKS:
        if rank.index == index:
            return rank