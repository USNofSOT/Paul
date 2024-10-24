import discord

def create_leaderboard_embed(bot, guild_id, data, title):
    """
    Creates a leaderboard embed.

    Args:
        bot: The bot instance.
        guild_id: The ID of the guild.
        data: The leaderboard data (list of tuples).
        title: The title of the embed.

    Returns:
        A discord.Embed object.
    """
    embed = discord.Embed(title=f"__{title}__")
    guild = bot.get_guild(guild_id)
    
    for rank, (member_id, value) in enumerate(data, 1):
        member = guild.get_member(member_id)  # Fetch the member object
        if member:
            member_name = member.display_name or member.name  # Use display name or name
            embed.add_field(name=f"{rank}. {member_name}", value=value, inline=False)
        else:
            embed.add_field(name=f"{rank}. Unknown User", value=value, inline=False)
    return embed



def create_master_embed(bot, guild_id, data, title):
    """
    Creates a leaderboard embed.

    Args:
        bot: The bot instance.
        guild_id: The ID of the guild.
        data: The leaderboard data (list of tuples).
        title: The title of the embed.

    Returns:
        A discord.Embed object.
    """
    embed = discord.Embed(title=f"__{title}__")
    guild = bot.get_guild(guild_id)

    # Split the data into two columns
    half_length = len(data) // 2
    first_column = data[:half_length]
    second_column = data[half_length:]

    # Add members to the embed in two columns
    for member_id_1, member_id_2 in zip(first_column, second_column):
        member_1 = guild.get_member(member_id_1)
        member_2 = guild.get_member(member_id_2)
        if member_1 and member_2:
            member_name_1 = member_1.display_name or member_1.name
            member_name_2 = member_2.display_name or member_2.name
            embed.add_field(name=f"{member_name_1}\u200b", value="\u200b", inline=True)
            embed.add_field(name=f"{member_name_2}\u200b", value="\u200b", inline=True)
        elif member_1:
            member_name_1 = member_1.display_name or member_1.name
            embed.add_field(name=member_name_1, value="\u200b", inline=True)
        elif member_2:
            member_name_2 = member_2.display_name or member_2.name
            embed.add_field(name=member_name_2, value="\u200b", inline=True)

    # If there's an odd number of members, add the last one
    if len(data) % 2 != 0:
        member_id = data[-1]
        member = guild.get_member(member_id)
        if member:
            member_name = member.display_name or member.name
            embed.add_field(name=member_name, value="\u200b", inline=True)

    return embed

def create_subclass_leaderboard_embed(bot, guild_id, top_helm, top_flex, top_cannoneer, top_carpenter, top_surgeon, top_grenadier):
    """
    Creates a leaderboard embed for subclass points.

    Args:
        bot: The bot instance.
        guild_id: The ID of the guild.
        top_helm: List of top members for Helm points.
        top_flex: List of top members for Flex points.
        top_cannoneer: List of top members for Cannoneer points.
        top_carpenter: List of top members for Carpenter points.
        top_surgeon: List of top members for Surgeon points.
        top_grenadier: List of top members for Grenadier points.

    Returns:
        A discord.Embed object.
    """
    embed = discord.Embed(title="__Top Subclass Points__")
    guild = bot.get_guild(guild_id)

    # Helper function to add subclass data to the embed
    def add_subclass_data(subclass_name, data):
        if data:
            # Get all members for this subclass
            member_data = []
            for member_id, value in data:
                member = guild.get_member(member_id)
                if member:
                    member_name = member.display_name or member.name
                    # Add zero-width spaces to prevent wrapping
                    member_data.append(f"{member_name}\u200b:\u200b {value}")
            embed.add_field(name=f"Top {subclass_name}", value="\n".join(member_data), inline=True)

    # Add data for each subclass
    add_subclass_data("Helm <:wheel:1256589625993068665>", top_helm)
    add_subclass_data("Flex <:sword:1256589612202332313>", top_flex)
    add_subclass_data("Cannoneer <:cannon:1256589581894025236>", top_cannoneer)
    add_subclass_data("Carpenter <:planks:1256589596473692272>", top_carpenter)
    add_subclass_data("Surgeon :adhesive_bandage:", top_surgeon)
    add_subclass_data("Grenadier <:athenakeg:1030819975730040832>", top_grenadier)

    return embed

def create_dual_leaderboard_embed(bot, guild_id, data1, title1, data2, title2):
    """
    Creates a leaderboard embed with two sets of data in two columns.

    Args:
        bot: The bot instance.
        guild_id: The ID of the guild.
        data1: The first leaderboard data (list of tuples).
        title1: The title of the first leaderboard.
        data2: The second leaderboard data (list of tuples).
        title2: The title of the second leaderboard.

    Returns:
        A discord.Embed object.
    """
    embed = discord.Embed(title=f"__{title1} and {title2}__")
    guild = bot.get_guild(guild_id)

    # Determine the maximum number of entries to display
    max_entries = max(len(data1), len(data2))

    # Create empty lists to store the formatted field values
    field_values_1 = []
    field_values_2 = []

    for rank in range(1, max_entries + 1):
        # Get data for the current rank from both lists
        member_id_1, value1 = data1[rank - 1] if rank <= len(data1) else (None, None)
        member_id_2, value2 = data2[rank - 1] if rank <= len(data2) else (None, None)

        # Fetch member objects
        member_1 = guild.get_member(member_id_1) if member_id_1 else None
        member_2 = guild.get_member(member_id_2) if member_id_2 else None

        # Construct field values
        field_value_1 = f"{rank}. {member_1.display_name or member_1.name}: {value1}" if member_1 else f"{rank}."
        field_value_2 = f"{rank}. {member_2.display_name or member_2.name}: {value2}" if member_2 else f"{rank}."

        # Add field values to the lists
        field_values_1.append(field_value_1)
        field_values_2.append(field_value_2)

    # Add fields to the embed with the formatted values
    embed.add_field(name=title1, value="\n".join(field_values_1), inline=True)
    embed.add_field(name=title2, value="\n".join(field_values_2), inline=True)

    return embed