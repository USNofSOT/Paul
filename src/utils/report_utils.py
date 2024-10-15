import discord

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
        "Citation Of Combat",
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

async def other_medals(member: discord.Member) -> list[str]:
    found_titles = []

    titles = [
        # High Ranking Medals
        "Medal of Honor",
        "Distinguished Service Cross",
        "Admiralty Medal",
        "Officer Improvement Ribbon",
        "Marine Exceptional Service Medal",
        "Medal of Exceptional Service",
        "Leadership Accolade",
        "Legion of Merit",
        "NCO Improvement Ribbon",
        "Valor and Courage",
        "Recruitment Ribbon",
        "Career Intelligence Medal",
        "Unit Commendation Medal",
    ]
    count = 0

    for role in member.roles:
        if role.name in titles:
            found_titles.append((titles.index(role.name), role.name))
            count += 1
        if count == 6:
            break
    found_titles.sort(key=lambda x: x[0])
    found_titles = [title[1] for title in found_titles]

    return found_titles

# Trigs: The code below here is super messy, so good luck trying to understand it.
# For usage, I refer you to the legacy codebase. Sowwy
# Probably want to rewrite it at some point

def get_role_in_list(member, role_list):
    for role in member.roles:
        if role.name in role_list:
            return role
    return None

def identify_role_index(ctx, member):
    listidentify = ['Squad Leader', 'Chief of Ship', 'First Officer', 'Commanding Officer', 'Fleet Commander',
                    'Master Chief Petty Officer of the Navy', 'Vice Admiral of the Navy', 'Admiral of the Navy']
    identify_role = get_role_in_list(member, listidentify)
    

    if identify_role is None:
        return None

    highest_ranking_role = None
    for role_name in listidentify:
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role in member.roles:
            highest_ranking_role = role
    if highest_ranking_role is None:
        return None

    for index, role_name in enumerate(listidentify):
        if highest_ranking_role.name == role_name:
            return index
    return None

def loa2_check(ctx, id, index):
    if "LOA-2" in id.display_name:
        return process_role_index(ctx, id, index)
    return True

def get_role_with_keyword(member, keyword):
    roles_with_keyword = [role for role in member.roles if keyword.lower() in role.name.lower()]
    if roles_with_keyword:
        return roles_with_keyword[0]
    return None

def process_role_index(ctx, member, role_index):
    if role_index == -1 or role_index == 7:
        return "Owns Server (No CO)"

    elif role_index == 6 or role_index == 5:
        admiral_role = discord.utils.get(ctx.guild.roles, name='Admiral of the Navy')
        if admiral_role is None:
            return None
        admiral_members = [m.id for m in admiral_role.members]
        if admiral_members and admiral_members[0] != member.id:
            next_in_command_member = ctx.guild.get_member(admiral_members[0])
            LOACheck = loa2_check(ctx, next_in_command_member, role_index + 1)
            if LOACheck == True:
                return [admiral_members[0]]
            else:
                return [admiral_members[0], LOACheck]
        return process_role_index(ctx, member, role_index + 1)


    elif role_index == 4:
        vice_admiral_role = discord.utils.get(ctx.guild.roles, name='Vice Admiral of the Navy')
        if vice_admiral_role is None:
            return process_role_index(ctx, member, role_index + 1)
        vice_admiral_members = [m.id for m in vice_admiral_role.members]
        if vice_admiral_members and vice_admiral_members[0] != member.id:
            next_in_command_member = ctx.guild.get_member(vice_admiral_members[0])
            LOACheck = loa2_check(ctx, next_in_command_member, role_index + 1)
            if LOACheck == True:
                return [vice_admiral_members[0]]
            else:
                return [vice_admiral_members[0], LOACheck]
        return process_role_index(ctx, member, role_index + 1)


    elif role_index == 3:
        fleet_role = get_role_with_keyword(member, "fleet")
        if fleet_role is None:
            return process_role_index(ctx, member, role_index + 1)
        fleet_members = [m.id for m in fleet_role.members]

        fleet_commander_role = discord.utils.get(ctx.guild.roles, name='Fleet Commander')
        if fleet_commander_role is None:
            return process_role_index(ctx, member, role_index + 1)
        fleet_commander_members = [m.id for m in fleet_commander_role.members]

        common_members = set(fleet_members) & set(fleet_commander_members)
        if common_members:
            next_in_command_id = common_members.pop()
            if next_in_command_id != member.id:
                next_in_command_member = ctx.guild.get_member(next_in_command_id)
                LOACheck = loa2_check(ctx, next_in_command_member, role_index + 1)
                if LOACheck == True:
                    return [next_in_command_id]
                else:
                    return [next_in_command_id, LOACheck]
        return process_role_index(ctx, member, role_index + 1)


    elif role_index == 2:
        ship_role = get_role_with_keyword(member, "USS")
        if ship_role is None:
            return process_role_index(ctx, member, role_index + 1)
        ship_members = [m.id for m in ship_role.members]

        ship_commander_role = discord.utils.get(ctx.guild.roles, name='Commanding Officer')
        if ship_commander_role is None:
            return process_role_index(ctx, member, role_index + 1)
        ship_commander_members = [m.id for m in ship_commander_role.members]

        common_members = set(ship_members) & set(ship_commander_members)
        if common_members:
            next_in_command_id = common_members.pop()
            if next_in_command_id != member.id:
                next_in_command_member = ctx.guild.get_member(next_in_command_id)
                LOACheck = loa2_check(ctx, next_in_command_member, role_index + 1)
                if LOACheck == True:
                    return [next_in_command_id]
                else:
                    return [next_in_command_id, LOACheck]
        return process_role_index(ctx, member, role_index + 1)


    elif role_index == 1:
        ship_role = get_role_with_keyword(member, "USS")
        if ship_role is None:
            return process_role_index(ctx, member, role_index + 1)
        ship_members = [m.id for m in ship_role.members]

        first_officer_role = discord.utils.get(ctx.guild.roles, name='First Officer')
        if first_officer_role is None:
            return process_role_index(ctx, member, role_index + 1)
        first_officer_members = [m.id for m in first_officer_role.members]

        common_members = set(ship_members) & set(first_officer_members)
        if common_members:
            next_in_command_id = common_members.pop()
            if next_in_command_id != member.id:
                next_in_command_member = ctx.guild.get_member(next_in_command_id)
                LOACheck = loa2_check(ctx, next_in_command_member, role_index + 1)
                if LOACheck == True:
                    return [next_in_command_id]
                else:
                    return [next_in_command_id, LOACheck]
        return process_role_index(ctx, member, role_index + 1)


    elif role_index == 0:
        ship_role = get_role_with_keyword(member, "USS")
        if ship_role is None:
            return process_role_index(ctx, member, role_index + 1)
        ship_members = [m.id for m in ship_role.members]

        chief_of_ship_role = discord.utils.get(ctx.guild.roles, name='Chief of Ship')
        if chief_of_ship_role is None:
            return process_role_index(ctx, member, role_index + 1)
        chief_of_ship_members = [m.id for m in chief_of_ship_role.members]

        common_members = set(ship_members) & set(chief_of_ship_members)
        if common_members:
            next_in_command_id = common_members.pop()
            if next_in_command_id != member.id:
                next_in_command_member = ctx.guild.get_member(next_in_command_id)
                LOACheck = loa2_check(ctx, next_in_command_member, role_index + 1)
                if LOACheck == True:
                    return [next_in_command_id]
                else:
                    return [next_in_command_id, LOACheck]
        return process_role_index(ctx, member, role_index + 1)


    elif role_index == None:
        squad_role = get_role_with_keyword(member, "squad")
        if squad_role is None:
            return process_role_index(ctx, member, 1)
        squad_members = [m.id for m in squad_role.members]

        squad_leader_role = discord.utils.get(ctx.guild.roles, name='Squad Leader')
        if squad_leader_role is None:
            return process_role_index(ctx, member, 1)
        squad_leader_members = [m.id for m in squad_leader_role.members]

        common_members = set(squad_members) & set(squad_leader_members)
        if common_members:
            next_in_command_id = common_members.pop()
            if next_in_command_id != member.id:
                next_in_command_member = ctx.guild.get_member(next_in_command_id)
                LOACheck = loa2_check(ctx, next_in_command_member, 1)
                if LOACheck == True:
                    return [next_in_command_id]
                else:
                    return [next_in_command_id, LOACheck]
        return process_role_index(ctx, member, 1)