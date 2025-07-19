import discord
from config.awards import MEDALS_AND_RIBBONS

async def tiered_medals(member: discord.Member) -> tuple[str, list[discord.Role]]:
    # Get tiered roles
    tiered_roles = []
    roles_dict = {r.id : r for r in member.roles}
    for category in MEDALS_AND_RIBBONS.tiered_awards:
        category_awards = getattr(MEDALS_AND_RIBBONS, category)
        for award in reversed(category_awards):
            if award.role_id in roles_dict:
                tiered_roles.append(roles_dict[award.role_id])
                break

    # Sort roles by position (order of precedence)
    result_roles = sorted(tiered_roles, key=lambda x : x.position, reverse=True)

    # Create string
    result = "".join([f"<@&{role.id}>\n" for role in result_roles])

    return result, result_roles

async def other_medals(member: discord.Member) -> tuple[list[str], list[discord.Role]]:
    titles = [
        # High Ranking Medals
        "Medal of Honor",
        "Distinguished Service Cross",
        "Admiralty Medal",
        "Valor and Courage",
        "Legion of Merit",
        "Marine Exceptional Service Medal",
        "Medal of Exceptional Service",
        "Officer Improvement Ribbon",
        "NCO Improvement Ribbon",
        "Leadership Accolade",
        "Recruitment Ribbon",
        "Career Intelligence Medal",
        "Unit Commendation Medal",
        "Legends of the Fleets",
        "Chart Your Destiny In The Light Of Sunrise",
    ]

    member_roles = {role.name : role for role in member.roles}
    found_roles = []

    for title in titles:
        if title in member_roles:
            found_roles.append(member_roles[title])
    
    found_roles.sort(key=lambda x: x.position, reverse=True) # sort by discord position / order of precedence
    found_titles = [role.name for role in found_roles]

    return found_titles, found_roles
