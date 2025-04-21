from __future__ import annotations

import logging

import discord

from src.config.ranks import RANKS
from src.data.structs import NavyRank

log = logging.getLogger(__name__)


def get_next_award(target: discord.Member, category_awards: [any]) -> any or None:
    """
    Given the current member, return the next award that the member will achieve.
    """
    member_role_ids = [role.id for role in target.roles]
    member_awards = [
        award for award in category_awards if award.role_id in member_role_ids
    ]
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


def get_current_award(target: discord.Member, category_awards: [any]) -> any:
    """
    Given the current member, return the award with the highest index that the member has.
    """
    highest_award = None
    member_role_ids = [role.id for role in target.roles]
    member_awards = [
        award for award in category_awards if award.role_id in member_role_ids
    ]
    for award in member_awards:
        if highest_award is None or award.threshold < highest_award.threshold:
            highest_award = award
    return highest_award


def has_award_or_higher(
    target: discord.Member, required_award, category_awards
) -> bool:
    """
    Check if the target has the required award or higher.
    """
    member_role_ids = [role.id for role in target.roles]
    member_awards = [
        award for award in category_awards if award.role_id in member_role_ids
    ]
    required_threshold = required_award.threshold
    log.info(
        "Checking if %s has the required award or higher: %s",
        target.display_name,
        required_award,
    )
    for award in member_awards:
        if award.threshold >= required_threshold:
            log.info(
                "%s has the required award or higher: %s - %s >= %s",
                target.display_name,
                award,
                award.threshold,
                required_threshold,
            )

            return True


def get_current_rank(target: discord.Member) -> NavyRank:
    """
    Given the current member, return the rank with the highest index that the member has.
    """
    highest_rank = None
    for rank in RANKS:
        if any(role.id in rank.role_ids for role in target.roles):
            if highest_rank is None or rank.index < highest_rank.index:
                highest_rank = rank
    return highest_rank


def get_rank_by_index(index: int) -> NavyRank:
    """
    Given a given index, return the corresponding NavyRank object
    """
    for rank in RANKS:
        if rank.index == index:
            return rank
