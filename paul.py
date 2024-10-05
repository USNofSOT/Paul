#Paul Bot Made for USNofSOT

#Imports
import asyncio
import datetime
import discord
import mariadb
import os
import re
from database_manager import DatabaseManager
from datetime import datetime, timezone
from discord import Intents, Client, Message
from discord.commands import option, Option
from discord.ext import commands
from dotenv import load_dotenv
from typing import Final


#Load token

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

#bot setup
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True

current_time = datetime.now(timezone.utc)

bot = discord.Bot(intents=intents)

# startup

@bot.event
async def on_ready():
    print(f'{bot.user} is now running!')

    # Sync commands globally (for all servers)
    await bot.tree.sync()
    print("Slash commands synced!")



#initiate db manager and commands class

db_manager = DatabaseManager()

# On Message Events  --- These happen passively as events happen on the server
@bot.event
async def on_message(message):

#Voyage Channel Work
    if message.channel.id == str(os.getenv('VOYAGE_LOG')):
        #Data to Variables

        host_id = message.author.id #Log Poster get voyage host credit
        log_id = message.id  # The message ID is the voyage log ID

        #Add Hosted count
        db_manager.increment_count(host_id, "hosted_count")  # Increment hosted count in Sailorinfo

        # Add a record to the Hosted table
        db_manager.log_hosted_data(log_id, host_id, 1, datetime.now(timezone.utc))  # Log the hosting record

        # Process mentioned users
        mentioned_users = set(message.mentions)  # Use a set to automatically deduplicate mentions
        for user in mentioned_users:
            db_manager.increment_count(user.id, "voyage_count")  # Increment voyage count in Sailorinfo
            # Log voyage record (without voyage_count)
            db_manager.log_voyage_data(message.id, user.id, 1, datetime.now(timezone.utc))
    else:
        return None


# Slash Commands

#ADDSUBCLASS
@bot.slash_command(name="addsubclass", description="Add subclass points for your log")
# @discord.default_permissions(moderate_members=True)
async def add_subclass(ctx, log_id: Option(str, "Paste in the ID of the log message")):
    global subclass_points

    try:
        log_id = int(log_id)
    except ValueError:
        await ctx.respond("Invalid log ID. Please provide a valid message ID.", ephemeral=True)
        return

    channel = bot.get_channel(logbook_channel_id)
    if not channel:
        await ctx.respond("Logbook channel not found.", ephemeral=True)
        return

    try:
        message = await channel.fetch_message(log_id)
    except discord.NotFound:
        await ctx.respond("Log message not found. Please provide a valid message ID.", ephemeral=True)
        return

    if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer", "Senior Non Commissioned Officer",
                                          "Non Commissioned Officer"]) and not check_testing(ctx):
        await ctx.respond("Only current voyage hosts can add to their logs!", ephemeral=True)
        return

    if (message.author != ctx.author and
            not check_permissions(ctx.author, ["Senior Officer", "Junior Officer"]) and not check_testing(ctx)):
        await ctx.respond(
            "You need to be the voyage host in order to do this command. If voyage host is unavailable, JO+ can do it.",
            ephemeral=True)
        return

    # Deleting duplicate subclass points before logging new data
    delete_duplicate_subclasses(log_id)

    content = message.content
    lines = content.split('\n')

    subclass_data = {}

    for line in lines:
        if '<@' in line and 'log' not in line:
            mention_index = line.find('<@')
            user_mention_part = line[mention_index:]
            parts = [part.strip() for part in re.split(r'[ ,\-–]', user_mention_part) if part.strip()]

            # Handle the 's after the first mention
            if len(parts) > 1 and parts[1].lower() == "'s":
                parts.pop(1)

            user_mention = parts[0]
            subclasses_raw = parts[1:]

            subclasses = [synonym_to_subclass.get(subclass_raw.strip().lower(), None) for subclass_raw in subclasses_raw
                          if synonym_to_subclass.get(subclass_raw.strip().lower())]

            if subclasses:
                subclass_data[user_mention] = subclasses

    if not subclass_data:
        await ctx.respond("No valid subclass data found in the log message.", ephemeral=True)
        return

    response_message = "Subclass points have been successfully added for:\n"
    end_response = ""

    for user_mention, subclasses in subclass_data.items():
        response_message += f"{user_mention}: {', '.join(subclasses)}\n"
        author_id = ctx.author.id
        log_link = f"https://discord.com/channels/{ctx.guild.id}/{logbook_channel_id}/{log_id}"

        try:
            target_id = int(user_mention.strip("<@!>'s:,*"))
        except ValueError:
            await ctx.respond(f"Invalid user mention: {user_mention}.", ephemeral=True)
            return

        for subclass in subclasses:
            count = 1
            db_manager.log_subclasses(author_id, log_link, target_id, subclass, count, datetime.utcnow())

        end_response += f"{user_mention}: Subclass points added.\n"

    await ctx.respond(response_message + "\n" + end_response.rstrip('\n'), ephemeral=True)

# Main Entry point  This function starts the bot.
def main() -> None:
    bot.run(token=TOKEN)

if __name__ == '__main__':
    main()