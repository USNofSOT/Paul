import discord
from data import TrainingRecord
from discord.ext.commands import Bot

from src.config.awards import MEDALS_AND_RIBBONS
from src.config.main_server import GUILD_ID
from src.config.subclasses import SUBCLASS_AWARDS
from src.data import Sailor
from src.data.repository.sailor_repository import SailorRepository
from src.data.structs import Award
from src.utils.ranks import rank_to_roles
from src.utils.report_utils import identify_role_index, process_role_index


def check_sailor(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> list[str]:
    # Assert these are the same person
    assert sailor.discord_id == member.id, "Sailor does not have the same ID as discord member."

    msg_strs = (
        # Check awards
        check_voyages(bot, interaction, sailor, member),
        check_hosted(bot, interaction, sailor, member),
        #FIXME: Add check for combat medals
        #FIXME: Add check for training medals
        #FIXME: Add check for recruiting medals
        #FIXME: Add check for attendance medals
        #FIXME: Add check for service stripes

        # Check subclasses
        check_cannoneer(bot, interaction, sailor, member),
        check_carpenter(bot, interaction, sailor, member),
        check_flex(bot, interaction, sailor, member),
        check_helm(bot, interaction, sailor, member),
        check_grenadier(bot, interaction, sailor, member),
        check_surgeon(bot, interaction, sailor, member),
    )

    return msg_strs

def check_voyages(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.voyage_count + sailor.force_voyage_count
    medals = MEDALS_AND_RIBBONS.voyages
    return _check_awards_by_type(bot, count, medals, interaction, sailor, member)

def check_hosted(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.hosted_count + sailor.force_hosted_count
    medals = MEDALS_AND_RIBBONS.hosted
    return _check_awards_by_type(bot, count, medals, interaction, sailor, member)

# check_combat

def check_training(bot : Bot, interaction: discord.Interaction, training_records: TrainingRecord, member: discord.Member) -> str:
    count = training_records.nrc_training_points + training_records.netc_training_points + training_records.st_training_points
    tiers = MEDALS_AND_RIBBONS.training
    return _check_awards_by_type(bot, count, tiers, interaction, member)

# check_recruiting

# check_attendance

# check_service

def check_cannoneer(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.cannoneer_points + sailor.force_cannoneer_points
    tiers = SUBCLASS_AWARDS.cannoneer
    return _check_awards_by_type(bot, count, tiers, interaction, member)

def check_carpenter(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.carpenter_points + sailor.force_carpenter_points
    tiers = SUBCLASS_AWARDS.carpenter
    return _check_awards_by_type(bot, count, tiers, interaction, member)

def check_flex(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.flex_points + sailor.force_flex_points
    tiers = SUBCLASS_AWARDS.flex
    return _check_awards_by_type(bot, count, tiers, interaction, member)

def check_helm(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.helm_points + sailor.force_helm_points
    tiers = SUBCLASS_AWARDS.helm
    return _check_awards_by_type(bot, count, tiers, interaction, member)

def check_grenadier(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.grenadier_points + sailor.force_grenadier_points
    tiers = SUBCLASS_AWARDS.grenadier
    return _check_awards_by_type(bot, count, tiers, interaction, member)

def check_surgeon(bot : Bot, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.surgeon_points + sailor.force_surgeon_points
    tiers = SUBCLASS_AWARDS.surgeon
    return _check_awards_by_type(bot, count, tiers, interaction, member)

def _check_awards_by_type(bot : Bot, count: int, medals: list[Award], interaction: discord.Interaction, member: discord.Member) -> str:
    msg_str = ""

    # Get award sailor is eligible for
    award = _find_highest_award(bot, count, medals)
    # Check if the user has a higher award
    if award is None:
        return msg_str

    # Check if member has award role already
    award_role = bot.get_guild(GUILD_ID).get_role(award.role_id)
    if award_role not in member.roles:
        msg_str = _award_message(bot, award, award_role, interaction, member)
    return msg_str

def _find_highest_award(bot : Bot, count : int, medals : list[Award]) -> None | Award:
    highest = None
    for medal in medals:
        if count >= medal.threshold:
            highest = medal
        else:
            break
    return highest

def _award_message(bot : Bot, award : Award | None, award_role : discord.Role, interaction: discord.Interaction, member: discord.Member) -> str:
    responsible_co = _get_responsible_co(bot, interaction, member, award.ranks_responsible)

    msg_str = ""
    msg_str += f"{member.mention} is eligible for **{bot.get_guild(GUILD_ID).get_role(award.role_id).name}**.\n"
    msg_str += f"\tRanks Responsible: {award.ranks_responsible}\n"
    if responsible_co is not None:
        sailor_repo = SailorRepository()
        co = sailor_repo.get_sailor(responsible_co.id)
        if co.award_ping_enabled:
            msg_str += f"\tResponsible CO: {responsible_co.mention}\n"
        else:
            msg_str += f"\tResponsible CO: {responsible_co.display_name}\n"
        sailor_repo.close_session()
    msg_str += f"\tDetails: {award.embed_url}\n"
    msg_str += "\n"
    return msg_str

def _get_responsible_co(bot : Bot, interaction:discord.Interaction, member: discord.Member, ranks_responsible: str) -> discord.Member | None:
    # Check if NETC/SPD Award
    for spd in ("Logistics","Media","NETC","NRC","NSC","Scheduling"):
        if spd in ranks_responsible:
            return None

    # Extract next in command
    role_index = identify_role_index(interaction, member)
    next_in_command = process_role_index(interaction, member, role_index)

    # Return None if process_role_index returns None or str
    if next_in_command is None:
        return None
    if isinstance(next_in_command,str):
        return None

    # Guarantee a list and take the last element (current CO)
    while isinstance(next_in_command,list):   #FIXME: this is the worst code ive ever written - Thunder
        next_in_command = next_in_command[-1]
    co_member = bot.get_guild(GUILD_ID).get_member(next_in_command)

    # Return early for "CO+"
    if ranks_responsible == "CO+":
        return co_member

    # Get roles for ranks responsible
    responsible_roles = rank_to_roles(ranks_responsible)

    # Check if CO has any roles
    co_role_ids = [r.id for r in co_member.roles]
    role_intersection = set(responsible_roles).intersection(set(co_role_ids))
    co_has_roles = len(role_intersection) > 0

    # If CO has roles, return them. Otherwise, go up the chain of command
    if co_has_roles:
        responsible_co=co_member
    else:
        responsible_co=_get_responsible_co(bot, interaction, co_member, ranks_responsible)
    return responsible_co
