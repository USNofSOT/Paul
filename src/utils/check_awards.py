import discord
from data import TrainingRecord

from src.config.awards import MEDALS_AND_RIBBONS
from src.config.subclasses import SUBCLASS_AWARDS
from src.data import Sailor
from src.data.repository.sailor_repository import SailorRepository
from src.data.structs import Award, SailorCO
from src.utils.ranks import rank_to_roles


def check_sailor(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> list[str]:
    # Assert these are the same person
    assert sailor.discord_id == member.id, "Sailor does not have the same ID as discord member."

    msg_strs = (
        # Check awards
        check_voyages(guild, interaction, sailor, member),
        check_hosted(guild, interaction, sailor, member),
        #FIXME: Add check for combat medals
        #FIXME: Add check for recruiting medals
        #FIXME: Add check for attendance medals
        #FIXME: Add check for service stripes

        # Check subclasses
        check_cannoneer(guild, interaction, sailor, member),
        check_carpenter(guild, interaction, sailor, member),
        check_flex(guild, interaction, sailor, member),
        check_helm(guild, interaction, sailor, member),
        check_grenadier(guild, interaction, sailor, member),
        check_surgeon(guild, interaction, sailor, member),
    )

    return msg_strs

def check_voyages(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.voyage_count + sailor.force_voyage_count
    medals = MEDALS_AND_RIBBONS.voyages
    return _check_awards_by_type(guild, count, medals, interaction, member)

def check_hosted(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.hosted_count + sailor.force_hosted_count
    medals = MEDALS_AND_RIBBONS.hosted
    return _check_awards_by_type(guild, count, medals, interaction, member)

# check_combat

def check_training(guild: discord.Guild, interaction: discord.Interaction, training_records: TrainingRecord, member: discord.Member) -> str:
    count = training_records.nrc_training_points + training_records.netc_training_points + training_records.st_training_points
    tiers = MEDALS_AND_RIBBONS.training
    return _check_awards_by_type(guild, count, tiers, interaction, member)

# check_recruiting

# check_attendance

# check_service

def check_cannoneer(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.cannoneer_points + sailor.force_cannoneer_points
    tiers = SUBCLASS_AWARDS.cannoneer
    return _check_awards_by_type(guild, count, tiers, interaction, member)

def check_carpenter(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.carpenter_points + sailor.force_carpenter_points
    tiers = SUBCLASS_AWARDS.carpenter
    return _check_awards_by_type(guild, count, tiers, interaction, member)

def check_flex(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.flex_points + sailor.force_flex_points
    tiers = SUBCLASS_AWARDS.flex
    return _check_awards_by_type(guild, count, tiers, interaction, member)

def check_helm(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.helm_points + sailor.force_helm_points
    tiers = SUBCLASS_AWARDS.helm
    return _check_awards_by_type(guild, count, tiers, interaction, member)

def check_grenadier(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.grenadier_points + sailor.force_grenadier_points
    tiers = SUBCLASS_AWARDS.grenadier
    return _check_awards_by_type(guild, count, tiers, interaction, member)

def check_surgeon(guild: discord.Guild, interaction: discord.Interaction, sailor: Sailor, member: discord.Member) -> str:
    count = sailor.surgeon_points + sailor.force_surgeon_points
    tiers = SUBCLASS_AWARDS.surgeon
    return _check_awards_by_type(guild, count, tiers, interaction, member)

def _check_awards_by_type(guild: discord.Guild, count: int, medals: list[Award], interaction: discord.Interaction, member: discord.Member) -> str:
    msg_str = ""

    # Get award sailor is eligible for
    award = _find_highest_award(count, medals)
    # Check if the user has a higher award
    if award is None:
        return msg_str

    # Check if member has award role already
    award_role = guild.get_role(award.role_id)
    if award_role not in member.roles:
        msg_str = _award_message(guild, award, award_role, interaction, member)
    return msg_str

def _find_highest_award(count : int, medals : list[Award]) -> None | Award:
    highest = None
    for medal in medals:
        if count >= medal.threshold:
            highest = medal
        else:
            break
    return highest

def _award_message(guild : discord.Guild, award : Award | None, award_role : discord.Role, interaction: discord.Interaction, member: discord.Member) -> str:
    # Check if SPD/NETC award
    is_SPD_NETC_award = any(kw in award.ranks_responsible for kw in ("Logistics","Media","NETC","NRC","NSC","Scheduling"))
    if is_SPD_NETC_award:
        responsible_co = award.ranks_responsible
    else:
        responsible_co = SailorCO(member, guild).for_awards(rank_to_roles(award.ranks_responsible))

    msg_str = ""
    msg_str += f"{member.mention} is eligible for **{guild.get_role(award.role_id).name}**.\n"
    msg_str += f"\tRanks Responsible: {award.ranks_responsible}\n"
    if is_SPD_NETC_award:
        msg_str += f"\tResponsible CO: {award.ranks_responsible}\n"
    elif responsible_co is None:
        pass
    elif isinstance(responsible_co, discord.Role):
        msg_str += f"\tResponsible Role: {responsible_co.name}\n"
    else:
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
