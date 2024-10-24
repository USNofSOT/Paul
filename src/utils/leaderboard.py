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
    embed = discord.Embed(title=title)
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
    embed = discord.Embed(title=title)
    guild = bot.get_guild(guild_id)
 
    for rank, (member_id) in enumerate(data, 1):
        member = guild.get_member(member_id)  # Fetch the member object
        if member:
            member_name = member.display_name or member.name  # Use display name or name
            embed.add_field(name=f"{rank}. {member_name}", value="\u200b", inline=False)
        else:
            embed.add_field(name=f"{rank}. Unknown User", value="\u200b", inline=False)
    return embed