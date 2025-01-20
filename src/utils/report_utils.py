import discord
from config.ranks_roles import DH_ROLES, VT_ROLES, RT_ROLES

async def tiered_medals(member: discord.Member) -> str:
    found_titles = []

    conduct_titles = [
        "Admirable Conduct Medal",
        "Meritorious Conduct Medal",
        "Honorable Conduct Medal",
        "Legion of Conduct",
        "Citation of Conduct",
    ]

    hosting_titles = [
        "Admirable Service Medal",
        "Legendary Service Medal",
        "Maritime Service Medal",
        "Sea Service Ribbon",
    ]

    voyaging_titles = [
        "Admirable Voyager Medal",
        "Meritorious Voyager Medal",
        "Honorable Voyager Medal",
        "Legion of Voyages",
        "Citation of Voyages",
    ]

    combat_titles = [
        "Admirable Combat Action",
        "Meritorious Combat Action",
        "Honorable Combat Action",
        "Legion of Combat",
        "Citation of Combat",
    ]

    training_titles = [
        "Admirable Training Ribbon",
        "Meritorious Training Ribbon",
        "Honorable Training Ribbon",
    ]

    time_titles = [
        "4 Months Service Stripes",
        "6 Months Service Stripes",
        "8 Months Service Stripes",
        "12 Months Service Stripes",
        "18 Months Service Stripes",
        "24 Months Service Stripes",
    ]

    attendance_titles = [
        "Citation of Attendance",
        "Legion of Attendance",
        "Meritorious Attendee Medal",
        "Admirable Attendee Medal",
    ]

    categories = [
        ("Hosting Titles", hosting_titles),
        ("Voyaging Titles", voyaging_titles),
        ("Combat Titles", combat_titles),
        ("Conduct Titles", conduct_titles),
        ("Time Titles", time_titles),
        ("Training Titles", training_titles),
        ("Attendance Titles", attendance_titles)
    ]

    result = ""

    for category_name, titles in categories:
        for role in member.roles:
            if role.name in titles:
                result += f"<@&{role.id}>\n"
                break

    return result

async def other_medals(member: discord.Member) -> (list[str], list[discord.Role]):
    found_titles = []
    found_roles = []

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
    ]
    count = 0

    member_roles = [role.name for role in member.roles]

    for title in titles:
        if title in member_roles:
            found_titles.append((count, title))
            found_roles.append(discord.utils.get(member.guild.roles, name=title))
            count += 1

    found_titles.sort(key=lambda x: x[0])
    found_titles = [title[1] for title in found_titles]

    return found_titles, found_roles
