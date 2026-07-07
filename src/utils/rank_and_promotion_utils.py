import logging

import discord

from src.config.ranks import RANKS
from src.config.ranks_roles import E2_ROLES
from src.data.structs import Award, NavyRank

log = logging.getLogger(__name__)


def _get_member_role_ids(target: discord.Member | None) -> set[int]:
    """
    Return role IDs for a guild member.

    Discord may return None or a User object instead of a Member when a voyage log
    mentions somebody who is no longer in the guild or is not cached. Those objects
    do not expose roles, so callers should treat them as having no rank/award roles.
    """
    return {role.id for role in getattr(target, "roles", [])}


def is_seaman_apprentice(target: discord.Member) -> bool:
    """
    Check if the member has the Seaman Apprentice role.
    """
    return E2_ROLES[1] in _get_member_role_ids(target)


def get_next_award(
        target: discord.Member,
        category_awards: [Award]
) -> Award or None:
    """
    Given the current member, return the next award that the member will achieve.
    """
    member_role_ids = _get_member_role_ids(target)
    member_awards = [award for award in category_awards if award.role_id in member_role_ids]
    highest_award = None
    for award in member_awards:
        if highest_award is None or award.threshold > highest_award.threshold:
            highest_award = award
    next_award = None
    for award in category_awards:
        if highest_award is None or award.threshold > highest_award.threshold:
            if next_award is None or award.threshold < next_award.threshold:
                next_award = award
    if highest_award is None and category_awards:
        return category_awards[0]
    return next_award


def get_current_award(
        target: discord.Member,
        category_awards: [Award]
) -> Award:
    """
    Given the current member, return the award with the highest index that the member has.
    """
    highest_award = None
    member_role_ids = _get_member_role_ids(target)
    member_awards = [award for award in category_awards if award.role_id in member_role_ids]
    for award in member_awards:
        if highest_award is None or award.threshold < highest_award.threshold:
            highest_award = award
    return highest_award


def has_award_or_higher(
    target: discord.Member,
    required_award: Award,
    category_awards: [Award]
) -> bool:
    """
    Check if the target has the required award or higher.
    """
    member_role_ids = _get_member_role_ids(target)
    member_awards = [award for award in category_awards if award.role_id in member_role_ids]
    required_threshold = required_award.threshold
    log.info(f"Checking if {target.display_name} has the required award or higher: {required_award}")
    for award in member_awards:
        if award.threshold >= required_threshold:
            log.info(f"{target.display_name} has the required award or higher: {award} - {award.threshold} >= {required_threshold}")
            return True


def get_current_rank(
        target: discord.Member
) -> NavyRank | None:
    """
    Given the current member, return the rank with the highest index that the member has.
    """
    highest_rank = None
    member_role_ids = _get_member_role_ids(target)
    for rank in RANKS:
        if any(role_id in rank.role_ids for role_id in member_role_ids):
            if highest_rank is None or rank.index < highest_rank.index:
                highest_rank = rank
    return highest_rank


 def get_current_rank_role_id(target: discord.Member) -> int | None:
    """
    Given the current member, return the specific applicable role ID for their rank.
    """
    highest_rank = get_current_rank(target)
    if not highest_rank:
        return None

    # Check if the user has the Seaman Apprentice role specifically
    if is_seaman_apprentice(target):
        return E2_ROLES[1]

    # Find the highest rank role ID the user actually possesses
    member_role_ids = _get_member_role_ids(target)
    for role_id in highest_rank.role_ids:
        if role_id in member_role_ids:
            return role_id

    return None


def get_rank_by_index(
        index: int
) -> NavyRank:
    """
    Given a given index, return the corresponding NavyRank object
    """
    for rank in RANKS:
        if rank.index == index:
            return rank
