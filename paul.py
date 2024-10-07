#Paul Bot Made for USNofSOT

""" Imports - 0 """
import asyncio
import datetime

import aiohttp
import discord
import os
import re
from database_manager import DatabaseManager
from datetime import datetime, timezone
from discord import app_commands
from discord.ext import commands, tasks
from dotenv import load_dotenv
from typing import Final

""" Bot Setup - 1"""
#Load token

load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')

#bot setup
current_time = datetime.now(timezone.utc)

bot = discord.ext.commands.Bot(command_prefix="!", intents=discord.Intents.all())

# Initialize DatabaseManager
db_manager = DatabaseManager()

# startup

@bot.event
async def on_ready():
    print(f'{bot.user} is now running!')
    try:
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands.")
    except Exception as e:
        print("An error with syncing application commands has occurred: ", e)

    try:
        voyage_log_channel_id = os.getenv('VOYAGE_LOGS')

        if voyage_log_channel_id is not None:
         channel = bot.get_channel(int(voyage_log_channel_id))
         async for message in channel.history(limit=50, oldest_first=False):  # Fetch the last 50
            await process_voyage_log(message)
            await asyncio.sleep(1)  # Introduce a 100second delay to prevent blocking
        else:
            print("Error: VOYAGE_LOG environment variable is not set.")

    except Exception as e:
        print("An error with processing existing voyage logs has occurred: ", e)




""" Passive Handlers - 2 """
# On Message Events  --- These happen passively as events happen on the server

@bot.event
async def on_message(message):
    # Voyage Channel Work
    if message.channel.id == 1291589712544268288:
        await process_voyage_log(message)
        print(f"Voyage log processed: {message.id}")

    else:
        # allows bot to process commands in messages
        await bot.process_commands(message)

# Remove voyages, and hosted on message deletion
@bot.event
async def on_message_delete(message):
    if message.channel.id == 1291589712544268288:
            log_id = message.id
            host_id = message.author.id
            participant_ids = [user.id for user in message.mentions]

            # Decrement hosted count
            db_manager.decrement_count(host_id, "hosted_count")
            db_manager.remove_hosted_entry( log_id)

            # Decrement voyage counts for participants
            for participant_id in participant_ids:
                db_manager.decrement_count(participant_id, "voyage_count")
                print(f"Voyage count delted: {participant_id}")
            # Remove entries from VoyageLog table (if necessary)
            db_manager.remove_voyage_log_entries(log_id)
            print(f"Voyage log deleted: {log_id}")
    else:
        # allows bot to process commands in messages
        await bot.process_commands(message)

#On Message Editing events
@bot.event
async def on_message_edit(before, after):
    if before.channel.id == 1291589712544268288:
        old_participant_ids = [user.id for user in before.mentions]
        new_participant_ids = [user.id for user in after.mentions]

        # Participants removed from the log
        removed_participants = set(old_participant_ids) - set(new_participant_ids)
        for participant_id in removed_participants:
            db_manager.decrement_count(participant_id, "voyage_count")
            db_manager.remove_voyage_log_entry(after.id, participant_id)
            print(f"Voyage log removed: {after.id}")

        # New participants added to the log
        added_participants = set(new_participant_ids) - set(old_participant_ids)
        for participant_id in added_participants:
            db_manager.increment_voyage_count(participant_id)
            # Add new entry to VoyageLog table if needed
            if not db_manager.voyage_log_entry_exists(after.id, participant_id):
                db_manager.log_voyage_data(after.id, participant_id, after.created_at)
                print(f"Voyage log added: {after.id}")

#Function that specifies Discord ID's for NSC Engineers
def is_allowed_user(ctx):
    allowed_user_ids = [646516242949341236, 690264788257079439]
    return ctx.author.id in allowed_user_ids

#NEW Compare message with DB after reboot PAUL
async def compare_message_with_db(message):
    # Get the current participants from the database
    db_participant_ids = db_manager.get_voyage_participants(message.id)

    # Get the participants from the current message mentions
    current_participant_ids = [user.id for user in message.mentions]

    # Find any participants that need to be added or removed
    removed_participants = set(db_participant_ids) - set(current_participant_ids)
    added_participants = set(current_participant_ids) - set(db_participant_ids)

    # Remove participants no longer mentioned
    for participant_id in removed_participants:
        db_manager.decrement_count(participant_id, "voyage_count")
        db_manager.remove_voyage_log_entry(message.id, participant_id)
        print(f"Voyage log removed: {message.id}, for participant: {participant_id}")

    # Add new participants that are now mentioned
    for participant_id in added_participants:
        db_manager.increment_voyage_count(participant_id)
        if not db_manager.voyage_log_entry_exists(message.id, participant_id):
            db_manager.log_voyage_data(message.id, participant_id, message.created_at)
            print(f"Voyage log added: {message.id}, for participant: {participant_id}")



""" Slash Commands - 3 """

# ADDSUBCLASS
@bot.tree.command(name="addsubclass", description="Add subclass points for your log")
@app_commands.describe(log_id="The ID of the log message")
async def addsubclass(interaction: discord.Interaction, log_id: str):
# Your command logic here
        await interaction.response.send_message(f"You provided log ID: {log_id}")

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

                subclasses = [synonym_to_subclass.get(subclass_raw.strip().lower(), None) for subclass_raw in
                              subclasses_raw
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

@bot.tree.command(name="addinfo", description="Add Gamertag or Timezone to yourself or another user")
@app_commands.describe(target="Select the user to add information to")
@app_commands.describe(gamertag="Enter the user's in-game username")
#@app_commands.describe(timezone="Enter the user's timezone manually (e.g., UTC+2) or leave empty to calculate automatically")
@app_commands.choices(timezone=[
                                   app_commands.Choice(name="UTC-12:00 (IDLW) - International Date Line West", value="UTC-12:00 (IDLW)"),
                                   app_commands.Choice(name="UTC-11:00 (NUT) - Niue Time, Samoa Standard Time", value="UTC-11:00 (NUT)"),
                                   app_commands.Choice(name="UTC-10:00 (HST) - Hawaii-Aleutian Standard Time", value="UTC-10:00 (HST)"),
                                   app_commands.Choice(name="UTC-09:00 (AKST) - Alaska Standard Time", value="UTC-09:00 (AKST)"),
                                   app_commands.Choice(name="UTC-08:00 (PST) - Pacific Standard Time", value="UTC-08:00 (PST)"),
                                   app_commands.Choice(name="UTC-07:00 (MST) - Mountain Standard Time", value="UTC-07:00 (MST)"),
                                   app_commands.Choice(name="UTC-06:00 (CST) - Central Standard Time", value="UTC-06:00 (CST)"),
                                   app_commands.Choice(name="UTC-05:00 (EST) - Eastern Standard Time", value="UTC-05:00 (EST)"),
                                   app_commands.Choice(name="UTC-04:00 (AST) - Atlantic Standard Time", value="UTC-04:00 (AST)"),
                                   app_commands.Choice(name="UTC-03:00 (BRT) - Brasilia Time, Argentina Standard Time", value="UTC-03:00 (BRT)"),
                                   app_commands.Choice(name="UTC-02:00 (FNT) - Fernando de Noronha Time", value="UTC-02:00 (FNT)"),
                                   app_commands.Choice(name="UTC-01:00 (CVT) - Cape Verde Time, Azores Standard Time", value="UTC-01:00 (CVT)"),
                                   app_commands.Choice(name="UTC±00:00 (UTC) - Coordinated Universal Time, Greenwich Mean Time", value="UTC±00:00 (UTC)"),
                                   app_commands.Choice(name="UTC+01:00 (CET) - Central European Time, West Africa Time", value="UTC+01:00 (CET)"),
                                   app_commands.Choice(name="UTC+02:00 (EET) - Eastern European Time, Central Africa Time", value="UTC+02:00 (EET)"),
                                   app_commands.Choice(name="UTC+03:00 (MSK) - Moscow Time, East Africa Time", value="UTC+03:00 (MSK)"),
                                   app_commands.Choice(name="UTC+04:00 (GST) - Gulf Standard Time, Samara Time", value="UTC+04:00 (GST)"),
                                   app_commands.Choice(name="UTC+05:00 (PKT) - Pakistan Standard Time, Yekaterinburg Time", value="UTC+05:00 (PKT)"),
                                   app_commands.Choice(name="UTC+06:00 (BST) - Bangladesh Standard Time, Omsk Time", value="UTC+06:00 (BST)"),
                                   app_commands.Choice(name="UTC+07:00 (ICT) - Indochina Time, Krasnoyarsk Time", value="UTC+07:00 (ICT)"),
                                   app_commands.Choice(name="UTC+08:00 (CST) - China Standard Time, Australian Western Standard Time", value="UTC+08:00 (CST)"),
                                   app_commands.Choice(name="UTC+09:00 (JST) - Japan Standard Time, Korea Standard Time", value="UTC+09:00 (JST)"),
                                   app_commands.Choice(name="UTC+10:00 (AEST) - Australian Eastern Standard Time", value="UTC+10:00 (AEST)"),
                                   app_commands.Choice(name="UTC+11:00 (VLAT) - Vladivostok Time, Solomon Islands Time", value="UTC+11:00 (VLAT)"),
                                   app_commands.Choice(name="UTC+12:00 (NZST) - New Zealand Standard Time, Fiji Time", value="UTC+12:00 (NZST)")
                                ])

@app_commands.describe(local_time="Enter your current local time (HH:MM) to calculate your timezone automatically")
async def addinfo(ctx, target: discord.Member = None, gamertag: str = None, timezone: str = None, local_time: str = None):
    await ctx.defer(ephemeral=True)

    # Default to the author if no target is provided
    if target is None:
        target = ctx.author

    # Initialize response
    response = f"Information added for {target.name}: \n"
    data_added = False

    # Process Gamertag
    if gamertag:
        db_manager.add_gamertag(target.id, gamertag)
        response += f"Gamertag: {gamertag}\n"
        data_added = True

    # If the user provided a timezone manually, use that
    if timezone:
        db_manager.add_timezone(target.id, timezone)
        response += f"Timezone: {timezone}\n"
        data_added = True

    # If no timezone was provided but local_time is provided, calculate the timezone automatically
    elif local_time:
        utc_offset, error = calculate_utc_offset(local_time)
        if error:
            await ctx.respond(f"Error: {error}")
            return
        else:
            db_manager.add_timezone(target.id, utc_offset)
            response += f"Timezone (calculated): {utc_offset}\n"
            data_added = True

    # Respond with the result
    if data_added:
        await ctx.respond(response)
    else:
        await ctx.respond("You didn't add any information.")

@bot.tree.command(name="updatemembers", description="Update the Sailorinfo table with current server members")
async def updatemembers(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)  # Defer the response for potentially long operation

    try:
        guild_id = interaction.guild.id  # Get the server ID
        guild = bot.get_guild(guild_id)  # Get the server object
        member_count = 0

        for member in guild.members:
            await asyncio.sleep(.1)  # Introduce a .1second delay to prevent blocking
            if not db_manager.discord_id_exists(member.id):
                db_manager.add_discord_id(member.id)
                member_count += 1

        await interaction.followup.send(f"Updated Sailorinfo with {member_count} new members.")

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")


""" Commands - 4"""




@bot.command(name="updatevoyagedb")
#@commands.has_any_role("Board of Admiralty")  # Check for roles
@commands.check(is_allowed_user)  # Also check for specific users
async def updatevoyagedb(ctx):
    try:
        # Syncing application commands (optional, you might not need this here)
        synced_commands = await bot.tree.sync()
        print(f"Synced {len(synced_commands)} commands.")

        voyage_log_channel_id = os.getenv('VOYAGE_LOGS')

        if voyage_log_channel_id is not None:
            channel = bot.get_channel(int(voyage_log_channel_id))
            async for message in channel.history(limit=None, oldest_first=True):
                await process_voyage_log(message)
                await asyncio.sleep(.5)  # Introduce a 1-second delay
        else:
            print("Error: VOYAGE_LOG environment variable is not set.")


    except Exception as e:
        print("An error with processing existing voyage logs has occurred: ", e)


""" Utilities - 5 """

@bot.command()
async def ping(ctx):
    ping_embed = discord.Embed(title="Ping", description="Pong!", color=discord.Color.blue())
    ping_embed.add_field(name=f"{bot.user.name}'s Latancy (ms)", value=f"{round(bot.latency * 1000)}", inline=False)
    ping_embed.set_footer(text=f"Pinged by {ctx.author.name}", icon_url=ctx.author.avatar.url)
    await ctx.send(embed=ping_embed)



# Function to calculate UTC offset based on provided local time
def calculate_utc_offset(local_time_str: str):
    # Parse the provided local time (expected in HH:MM format)
    try:
        local_time = datetime.strptime(local_time_str, "%H:%M")
    except ValueError:
        return None, "Invalid time format. Please use HH:MM (24-hour format)."

    # Get the current UTC time
    utc_now = datetime.now(timezone.utc)
    local_now = datetime.now()

    # Adjust the current local time to match the user's provided local time
    adjusted_local_time = local_now.replace(hour=local_time.hour, minute=local_time.minute, second=0, microsecond=0)

    # Calculate the difference between provided local time and UTC time
    utc_offset = adjusted_local_time - utc_now

    # Calculate hours and minutes from the time delta
    hours_offset = int(utc_offset.total_seconds() // 3600)
    minutes_offset = int((utc_offset.total_seconds() % 3600) // 60)

    # Format the offset (e.g., UTC+2 or UTC-5)
    sign = "+" if hours_offset >= 0 else "-"
    formatted_offset = f"UTC{sign}{abs(hours_offset):02d}:{abs(minutes_offset):02d}"

    return formatted_offset, None

#subroutine to check if a voyage log already exists, and processes it if it does not.
async def process_voyage_log(message):
    log_id = message.id
    host_id = message.author.id
    log_time = message.created_at
    participant_ids = []
    for user in message.mentions:
        participant_ids.append(user.id)

    #print(f" logid: {log_id} hostid: {host_id} time: {log_time}") # Used to view data on console as it is processed.

    # 1. Check if the log_id already exists in the database
    if db_manager.hosted_log_id_exists(log_id):
        return  # Skip if the log has already been processed

    # 2. If not, process the log as you did in on_message
    db_manager.log_hosted_data(log_id, host_id, log_time)
    # 3.Log Voyage Count

    voyage_data = []
    for participant_id in participant_ids:
        if not db_manager.voyage_log_entry_exists(log_id, participant_id):
                voyage_data.append((log_id, participant_id, log_time))
                db_manager.increment_voyage_count(participant_id)

    # Batch insert voyage data
    db_manager.batch_log_voyage_data(voyage_data)

# Main Entry point  This function starts the bot.
def main() -> None:
    bot.run(token=TOKEN)

if __name__ == '__main__':
    main()
