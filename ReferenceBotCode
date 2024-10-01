# !/home/Angryhamdog/.virtualenvs/myvenv/bin/python

# https://discord.com/oauth2/authorize?client_id=1145532919666987149&permissions=8&scope=bot+applications.commands
# THIS IS THE PRIVATE LINK TO ADD THE BOT TO A NEW SERVER. ADDING IT TO ANOTHER SERVER MAY CAUSE ISSUES DUE TO THE BOTS PROGRAMMING.

import discord
import asyncio
import logging
from discord.commands import option, Option
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import os
import re

current_time = datetime.now(timezone.utc)

intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.members = True

bot = discord.Bot(intents=intents)

import os

# SHould be the proper directory
os.chdir("/home/container/")

# Print the current working directory as a check
print(f"Current working directory: {os.getcwd()}")

# List files in the current working directory as a check
print("Files in the current directory:")
print(os.listdir(os.getcwd()))

# List of required files
required_files = [
    "Subclasses.txt", "Voyages.txt", "Hosted.txt", "Forceadd.txt",
    "Coins.txt", "ModNotes.txt", "Auditlogs.txt", "Settings.txt",
    "Gamertags.txt", "Timezones.txt"
]

# Check if all required files exist
missing_files = [file_name for file_name in required_files if not os.path.exists(file_name)]

# Print found files and missing files
print(f"Found files: {[file_name for file_name in required_files if os.path.exists(file_name)]}")
print(f"Missing files: {missing_files}")

if missing_files:
    missing_files_str = ', '.join(missing_files)
    raise FileNotFoundError(f"Required files missing: {missing_files_str}")


# ^To make sure the files are found before moving on in regards to the subclass2.txt error

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')


@bot.event
async def on_raw_message_edit(payload):
    '''
    # This is code to get the message that was before if it was cached, meaning before a bot reset.
    # It's not actually needed for any reason we're currently doing but I'd like to leave it here.
    if payload.cached_message:
        before = payload.cached_message
        print(before)
    else:
        before = None
        print(before)
    '''

    if 'channel_id' in payload.data and payload.data['channel_id'] == str(935343526626078850):
        channel = bot.get_channel(int(payload.data['channel_id']))

        after = await channel.fetch_message(payload.message_id)

        delete_duplicate_voyage(after.id)
        await process_voyage_data(after)


@bot.event
async def on_message(message):
    if message.channel.id == 935343526626078850:
        await process_voyage_data(message)

    if message.content == '!update-database' and await check_testing(message):
        channel_id = 935343526626078850
        channel = bot.get_channel(channel_id)

        if os.path.exists("Voyages.txt"):
            os.remove("Voyages.txt")
            print(f"File Voyages.txt has been deleted.")
        else:
            print(f"File Voyages.txt does not exist. No file to delete.")

        if os.path.exists("Hosted.txt"):
            os.remove("Hosted.txt")
            print(f"File Hosted.txt has been deleted.")
        else:
            print(f"File Hosted.txt does not exist. No file to delete.")

        with open("Voyages.txt", 'w') as file:
            pass

        with open("Hosted.txt", 'w') as file:
            pass

        async for message in channel.history(limit=None, oldest_first=True):
            await process_voyage_data(message)

    if message.content == '!grab-top' and await check_testing(message) and check_permissions(message.author,
                                                                                             ["Logistics Department"]):
        top_roles = {
            "Master Carpenter": "carpenter",
            "Master Flex": "flex",
            "Master Cannoneer": "cannoneer",
            "Master Helm": "helm",
            "Grenadier": "grenadier",
            "Field Surgeon": "surgeon"
        }

        top_subclasses = {role: [] for role in top_roles}

        # Iterate over each role and collect top 3 subclass points
        for role_name, subclass_name in top_roles.items():
            members_with_points = []

            # Fetch subclass points for all members
            for member in message.guild.members:
                if any(role.name == role_name for role in member.roles):
                    subclass_points = await get_subclass_points(member)
                    print(str(member) + str(subclass_points))
                    index = list(top_roles.values()).index(subclass_name)
                    points = subclass_points[index]
                    if points > 0:
                        members_with_points.append((member.name, points))

            # Sort members by subclass points and take top 3
            members_with_points.sort(key=lambda x: x[1], reverse=True)
            top_members = members_with_points[:3]

            # Format top members
            top_members_formatted = [f"{member[0]}: {member[1]}" for member in top_members]
            top_subclasses[role_name] = top_members_formatted

        # Top hoster and top voyager
        top_hosters = []
        top_voyagers = []

        # Check members with the "Legendary Service Medal" for hosted
        for member in message.guild.members:
            if any(role.name == "Legendary Service Medal" for role in member.roles):
                hosted_count = await get_hosted_info(member)
                if hosted_count[2] > 0:
                    top_hosters.append((member.name, hosted_count[2]))

        # Sort and get the top 3 hosters
        top_hosters.sort(key=lambda x: x[1], reverse=True)
        top_hosters_formatted = [f"{hoster[0]}: {hoster[1]}" for hoster in top_hosters[:3]]

        # Check members with the "Admirable Voyager Medal" for voyages
        for member in message.guild.members:
            if any(role.name == "Admirable Voyager Medal" for role in member.roles):
                voyage_count = await get_voyage_info(member)
                if voyage_count[2] > 0:
                    top_voyagers.append((member.name, voyage_count[2]))

        # Sort and get the top 3 voyagers
        top_voyagers.sort(key=lambda x: x[1], reverse=True)
        top_voyagers_formatted = [f"{voyager[0]}: {voyager[1]}" for voyager in top_voyagers[:3]]

        # Check for Subclass Masters
        subclass_masters = []
        required_roles = ["Master Carpenter", "Master Flex", "Master Cannoneer", "Master Helm"]
        for member in message.guild.members:
            if all(any(role.name == req_role for role in member.roles) for req_role in required_roles):
                subclass_masters.append(member.name)

        subclass_masters_formatted = [f"{master}" for master in subclass_masters]

        # Send the results
        if top_hosters_formatted:
            await message.channel.send(f"Top 3 Hosters:\n" + "\n".join(top_hosters_formatted))
        if top_voyagers_formatted:
            await message.channel.send(f"Top 3 Voyagers:\n" + "\n".join(top_voyagers_formatted))
        if subclass_masters_formatted:
            await message.channel.send(f"Subclass Masters:\n" + "\n".join(subclass_masters_formatted))

        # Send the top 3 subclass points for each role
        for role_name, top_members in top_subclasses.items():
            if top_members:
                await message.channel.send(f"Top 3 in {role_name}:\n" + "\n".join(top_members))

    if message.content.startswith('!voyage-together'):
        await handle_voyage_together(message)

    if message.content.startswith('!top-3'):
        await handle_voyage_together_top(message)


    elif message.author.id == 713484585874227220 and message.content == '!offserver':
        await message.delete()
        embedVar = discord.Embed(title="Bot is off-server",
                                 description=f"All voyages and subclass points may be non-existant or removed for the time being.\nIf you need to do a command, especially **add subclass points**, please ping hamdog beforehand to avoid failure during adding data.\nThis doesn't mean give him all the info, just wait for him to respond and say that your good to go.",
                                 color=discord.Color.red())
        await message.channel.send(embed=embedVar)


def log_forceadd(target_id, type, amount, moderator_id, timestamp):
    with open("Forceadd.txt", "a") as file:
        file.write(f"{target_id} - {type} - {amount} - {moderator_id} - {timestamp}")


def log_voyage_data(log_id, target_id, amount, log_time):
    with open("Voyages.txt", "a") as file:
        file.write(f"{log_id} - {target_id} - {amount} - {log_time}\n")


def log_hosted_data(log_id, host_id, amount, log_time):
    with open("Hosted.txt", "a") as file:
        file.write(f"{log_id} - {host_id} - {amount} - {log_time}\n")


def delete_duplicate_subclasses(log_id):
    log_id = f"https://discord.com/channels/933907909954371654/935343526626078850/{log_id}"
    with open("Subclasses.txt", "r+") as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            parts = line.strip().split(" - ")
            if len(parts) > 1 and parts[1] != log_id:
                file.write(line)
        file.truncate()


def delete_duplicate_voyage(log_id):
    print("Deleting duplicates for log_id:", log_id)

    with open("Voyages.txt", "r+") as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            parts = line.strip().split(" - ")
            if int(parts[0]) != log_id:
                file.write(line)
            else:
                print("Deleted line:", line.strip())
        file.truncate()

    with open("Hosted.txt", "r+") as file:
        lines = file.readlines()
        file.seek(0)
        for line in lines:
            parts = line.strip().split(" - ")
            if int(parts[0]) != log_id:
                file.write(line)
            else:
                print("Deleted line:", line.strip())
        file.truncate()


async def process_voyage_data(message):
    print("processing")
    mentions = message.mentions
    if len(mentions) <= 1:
        return

    processed_members = set()

    for mention in mentions:
        if mention.id not in processed_members:
            processed_members.add(mention.id)
            if mention.id == message.author.id:
                log_hosted_data(message.id, mention.id, "1", message.created_at)
            log_voyage_data(message.id, mention.id, "1", message.created_at)


async def handle_voyage_together(message):
    parts = message.content.split()
    if len(parts) != 3:
        await message.channel.send("Please provide exactly two IDs.")
        return

    member1_id = int(re.sub(r'\D', '', parts[1]))
    member2_id = int(re.sub(r'\D', '', parts[2]))

    guild = message.guild
    member1 = guild.get_member(member1_id)
    member2 = guild.get_member(member2_id)

    # Get names or use ID if not in server
    member1_name = member1.display_name if member1 else f"User{member1_id}"
    member2_name = member2.display_name if member2 else f"User{member2_id}"

    voyage_count, voyage_links = count_shared_voyages(member1_id, member2_id)

    message_header = f"Users {member1_name} and {member2_name} have been on the same voyage {voyage_count} times.\n\nLinks:\n"
    max_message_length = 2000
    links_message = message_header
    for link in voyage_links:
        if len(links_message) + len(link) + 1 > max_message_length:
            await message.channel.send(links_message)
            links_message = link + "\n"
        else:
            links_message += link + "\n"
    if links_message:
        await message.channel.send(links_message)


def count_shared_voyages(member1_id, member2_id):
    voyage_count = 0
    voyage_logs = {}
    voyage_links = []
    guild_id = '933907909954371654'
    channel_id = '935343526626078850'

    with open("Voyages.txt", "r") as file:
        for line in file:
            parts = line.strip().split(" - ")
            if len(parts) >= 4:
                log_id, member, change, time = parts
                file_member_id = int(member)

                if log_id not in voyage_logs:
                    voyage_logs[log_id] = set()

                voyage_logs[log_id].add(file_member_id)

    for log_id, members in voyage_logs.items():
        if member1_id in members and member2_id in members:
            voyage_count += 1
            voyage_links.append(f"https://discord.com/channels/{guild_id}/{channel_id}/{log_id}")

    return voyage_count, voyage_links


async def handle_voyage_together_top(message):
    parts = message.content.split()
    if len(parts) != 2:
        await message.channel.send("Please provide exactly one ID.")
        return

    target_member_id = int(re.sub(r'\D', '', parts[1]))

    top_users = count_top_shared_voyages(target_member_id)

    guild = message.guild
    target_member = guild.get_member(target_member_id)
    target_member_name = target_member.display_name if target_member else f"User{target_member_id}"

    message_header = f"Top users who have shared the most voyages with {target_member_name}:\n\n"
    max_message_length = 2000
    links_message = message_header
    for user, count in top_users:
        user_member = guild.get_member(user)
        user_name = user_member.display_name if user_member else f"User{user}"
        user_message = f"{user_name}: {count} voyages\n"
        if len(links_message) + len(user_message) > max_message_length:
            await message.channel.send(links_message)
            links_message = user_message
        else:
            links_message += user_message

    if links_message:
        await message.channel.send(links_message)


def count_top_shared_voyages(target_member_id):
    voyage_logs = {}
    shared_counts = {}

    with open("Voyages.txt", "r") as file:
        for line in file:
            parts = line.strip().split(" - ")
            if len(parts) >= 4:
                log_id, member, change, time = parts
                file_member_id = int(member)
                if log_id not in voyage_logs:
                    voyage_logs[log_id] = set()
                voyage_logs[log_id].add(file_member_id)

    # Create a list of all current members in the guild
    guild = discord.utils.get(bot.guilds, id=933907909954371654)  # Replace with your guild ID
    current_members = {member.id: member for member in guild.members}

    # Count shared voyages with current members only
    for log_id, members in voyage_logs.items():
        if target_member_id in members:
            for member in members:
                if member != target_member_id and member in current_members:
                    if member not in shared_counts:
                        shared_counts[member] = 0
                    shared_counts[member] += 1

    top_users = sorted(shared_counts.items(), key=lambda item: item[1], reverse=True)[:3]

    return top_users


@bot.event
async def on_member_update(before, after):
    guild = after.guild
    added_roles = [role.id for role in after.roles if role not in before.roles]
    if added_roles:
        for role_id in added_roles:
            async for entry in guild.audit_logs(limit=1):
                admin_id = entry.user.id
            await log_event(f"{after.id} - Role Added - {role_id} - {admin_id} - {datetime.utcnow()}")

    removed_roles = [role.id for role in before.roles if role not in after.roles]
    if removed_roles:
        for role_id in removed_roles:
            async for entry in guild.audit_logs(limit=1):
                admin_id = entry.user.id
            await log_event(f"{after.id} - Role Removed - {role_id} - {admin_id} - {datetime.utcnow()}")

    if before.nick != after.nick:
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
            if entry.target.id == after.id:
                admin_id = entry.user.id
                await log_event(
                    f"{after.id} - Nickname Change - {before.nick} - {after.nick} - {admin_id} - {datetime.utcnow()}")

    if not before.timed_out and after.timed_out:
        joined_at = after.communication_disabled_until
        totaltime = format_time(get_time_difference_future(joined_at))

        guild = after.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
            admin_id = entry.user.id

        await log_event(f"{after.id} - Timed Out - {totaltime} - {admin_id} - {datetime.utcnow()}")


    elif before.timed_out and not after.timed_out:
        guild = after.guild
        async for entry in guild.audit_logs(limit=1, action=discord.AuditLogAction.member_update):
            admin_id = entry.user.id

        await log_event(f"{after.id} - Untimed Out - {admin_id} - {datetime.utcnow()}")


@bot.event
async def on_member_remove(member):
    await log_event(f"{member.id} - Member Left - None - {datetime.utcnow()}")


@bot.event
async def on_member_ban(guild, user):
    async for entry in guild.audit_logs(action=discord.AuditLogAction.ban, limit=1):
        if entry.target.id == user.id:
            executor = entry.user
            break
    else:
        executor = "Unknown"

    await log_event(f"{user.id} - Member Banned - {executor} - {datetime.utcnow()}")


@bot.event
async def on_member_unban(guild, user):
    async for entry in guild.audit_logs(action=discord.AuditLogAction.unban, limit=1):
        if entry.target.id == user.id:
            executor = entry.user
            break
    else:
        executor = "Unknown"

    await log_event(f"{user.id} - Member Unbanned - {executor} - {datetime.utcnow()}")


@bot.event
async def on_member_kick(member):
    async for entry in member.guild.audit_logs(action=discord.AuditLogAction.kick, limit=1):
        if entry.target.id == member.id:
            executor = entry.user
            break
    else:
        executor = "Unknown"

    await log_event(f"{member.id} - Member Kicked - {executor} - {datetime.utcnow()}")


subclasses = ["Carpenter", "Helm", "Flex", "Cannoneer", "Gunner", "Surgeon", "Grenadier"]


async def get_subclasses(ctx: discord.AutocompleteContext):
    return [subclass for subclass in subclasses if subclass.startswith(ctx.value.lower())]


COINS = ["Commanders Challenge Coin", "Regular Challenge Coin"]


async def get_coin(ctx: discord.AutocompleteContext):
    return [level for level in COINS if level.startswith(ctx.value.lower())]


async def get_levels(ctx: discord.AutocompleteContext):
    levels = ["default", "moderation", "promotion"]
    return [level for level in levels if level.lower().startswith(ctx.value.lower())]


@bot.slash_command(name="addcoin", description="Check information of a user or all users in a role")
# @discord.default_permissions(mute_members=True)
@option("target", description="Select the user to add your challenge coin to")
@option("type", description="Choose view", autocomplete=get_coin)
async def addcoin(ctx, target: discord.Member, type):
    if not check_permissions(ctx.author,
                             ["Senior Officer", "Junior Officer"]) and not ctx.author.id == 713484585874227220:
        await ctx.respond("You don't have permissions to give challenge coins!", ephemeral=True)
        return

    if type == "Regular Challenge Coin":
        display_name = ctx.author.display_name.split()[-1]
        log_coin(target.id, "Regular Challenge Coin", ctx.author.id, display_name)
        await ctx.respond(f"Added a challenge coin to <@{target.id}>", ephemeral=True)
    elif type == "Commanders Challenge Coin":
        if not check_permissions(ctx.author, ["Senior Officer"]):
            await ctx.respond("You don't have permissions to give a commanders challenge coin!", ephemeral=True)
        else:
            display_name = ctx.author.display_name.split()[-1]
            log_coin(target.id, "Commanders Challenge Coin", ctx.author.id, display_name)
            await ctx.respond(f"Added a commanders challenge coin to <@{target.id}>", ephemeral=True)
    else:
        await ctx.respond("Invalid type of coin, please use the autocomplete to add them", ephemeral=True)


@bot.slash_command(name="addinfo", description="Add Gamertag or Timezone to yourself or another user")
@option("target", description="Select the user to add information to")
@option("gamertag", description="Enter the users in-game username")
@option("timezone", description="Enter the users timezone")
async def addinfo(ctx, target: discord.Member, gamertag: str = None, timezone: str = None):
    await ctx.defer(ephemeral=True)
    if not target:
        target = ctx.author

    allowed_roles = ["Senior Officer", "Junior Officer", "Senior Non Commissioned Officer", "NRC Department"]
    author_roles = [role.name for role in ctx.author.roles]

    if not any(role in allowed_roles for role in
               author_roles) and ctx.author != target and not ctx.author.id == 713484585874227220:
        await ctx.respond(
            "Hey, you're not allowed to do that! Only SNCO+ and NRC are allowed to edit other sailors information.")
        return

    target_id = target.id

    if gamertag:
        with open("Gamertags.txt", "a") as file:
            file.write(f"{target_id} - {gamertag}\n")

    if timezone:
        with open("Timezones.txt", "a") as file:
            file.write(f"{target_id} - {timezone}\n")

    if gamertag and timezone:
        await ctx.respond(f"Information added for {target.name}: \nGamertag: {gamertag}\nTimezone: {timezone}")
    elif gamertag:
        await ctx.respond(f"Information added for {target.name}: \nGamertag: {gamertag}")
    elif timezone:
        await ctx.respond(f"Information added for {target.name}: \nTimezone: {timezone}")
    else:
        await ctx.respond(f"You didn't add anything...")


@bot.slash_command(name="addnote", description="Add a moderation note to a user (SNCO+)")
# @discord.default_permissions(manage_messages=True)
@option("target", description="Select the user to add the note to")
@option("note", description="Write the note to add to the user")
async def addnote(ctx, target: discord.Member, note: str):
    required_roles = {"Senior Officer", "Junior Officer", "Senior Non Commissioned Officer"}
    executor_roles = {role.name for role in ctx.author.roles}

    if not any(role in required_roles for role in executor_roles) and not ctx.author.id == 713484585874227220:
        await ctx.respond("You do not have the necessary permissions to use this command. (SNCO+)", ephemeral=True)
        return

    target_roles = {role.name for role in target.roles}
    if any(role in required_roles for role in target_roles):
        await ctx.respond(
            "The target has a role high enough to see your note by checking their own moderation report. If you are sure, please type `confirm` in the channel.",
            ephemeral=True)

        def check(m):
            return m.content.lower() == 'confirm' and m.author == ctx.author and m.channel == ctx.channel

        try:
            confirmation = await bot.wait_for('message', check=check, timeout=60.0)
            if confirmation:
                await confirmation.delete()
                await add_note_to_file(target.id, ctx.author.id, note)
                await ctx.respond(f"Note confirmed and added for {target.mention}: {note}", ephemeral=True)
        except asyncio.TimeoutError:
            await ctx.respond("Confirmation timed out. Note not added.", ephemeral=True)
    else:
        await add_note_to_file(target.id, ctx.author.id, note)
        await ctx.respond(f"Note added for {target.mention}: {note}", ephemeral=True)



@bot.slash_command(name="check_awards", description="Check awards to ensure everyone is up-to-date")
@option("target_role", description="Select the role to check! Ships and squads work best.")
async def check_awards(ctx, target_role: discord.Role = None):
    logging.info(f"check_awards command invoked by {ctx.author.display_name}")
    await ctx.defer(ephemeral=True)

    async def process_member(member):
        try:
            carpenter, flex, cannoneer, helmsman, grenadier, surgeon = await get_subclass_points(member)
            points = {
                "carpenter": carpenter,
                "flex": flex,
                "cannoneer": cannoneer,
                "helm": helmsman,
                "grenadier": grenadier,
                "surgeon": surgeon
            }

            def get_role(subclass, points):
                if subclass in ["carpenter", "flex", "helm", "cannoneer"]:
                    if points >= 25:
                        return f"Master {subclass.capitalize()}"
                    elif points >= 15:
                        return f"Pro {subclass.capitalize()}"
                    elif points >= 5:
                        return f"Adept {subclass.capitalize()}"
                elif subclass == "grenadier" and points >= 10:
                    return "Grenadier"
                elif subclass == "surgeon" and points >= 5:
                    return "Field Surgeon"
                return None

            required_roles = {subclass: get_role(subclass, points[subclass]) for subclass in points}
            user_roles = [role.name for role in member.roles]
            missing_roles = ""
            target_id = member.id

            for subclass, role in required_roles.items():
                if role:
                    if role in user_roles:
                        pass
                    else:
                        missing_roles += f"<@{target_id}> is missing the {role}\n"

            voyages_info = await get_voyage_info(member)
            hosted_info = await get_hosted_info(member)
            hosted_value = hosted_info[2]
            voyages_value = voyages_info[2]

            hosted_awards = {
                200: "Admirable Service Medal",
                100: "Legendary Service Medal",
                50: "Maritime Service Medal",
                25: "Sea Service Ribbon"
            }

            voyages_awards = {
                200: "Admirable Voyager Medal",
                100: "Meritorious Voyager Medal",
                50: "Honorable Voyager Medal",
                25: "Legion of Voyages",
                5: "Citation of Voyages"
            }

            highest_hosted_award = None
            for value, award in hosted_awards.items():
                if hosted_value >= value:
                    highest_hosted_award = award
                    break

            highest_voyages_award = None
            for value, award in voyages_awards.items():
                if voyages_value >= value:
                    highest_voyages_award = award
                    break

            if highest_hosted_award and highest_hosted_award not in user_roles:
                missing_roles += f"<@{target_id}> is missing the {highest_hosted_award}\n"

            if highest_voyages_award and highest_voyages_award not in user_roles:
                missing_roles += f"<@{target_id}> is missing the {highest_voyages_award}\n"

            return missing_roles
        except Exception as e:
            logging.error(f"Error processing member {member.display_name}: {e}")
            return f"Error processing member {member.display_name}: {e}"

    try:
        missing_roles_list = []
        if target_role:
            for member in target_role.members:
                missing_roles_list.append(await process_member(member))
        else:
            missing_roles_list.append(await process_member(ctx.author))

        missing_roles = "".join(missing_roles_list)

        if missing_roles:
            await ctx.respond(missing_roles, ephemeral=True)
        else:
            await ctx.respond("All awards are up-to-date.", ephemeral=True)
    except Exception as e:
        logging.error(f"Error in check_awards command: {e}")
        await ctx.respond("An error occurred while checking awards. Please try again later.", ephemeral=True)


@bot.slash_command(name="check_squads", description="Check squads to ensure all JE are in a squad")
@option("target", description="Select the role to check for members missing a squad")
async def check_squads(ctx, target: discord.Role = None):
    await ctx.defer(ephemeral=True)
    squad_keyword = "Squad"
    junior_enlisted_role_name = "Junior Enlisted"

    junior_enlisted_role = discord.utils.get(ctx.guild.roles, name=junior_enlisted_role_name)
    if not junior_enlisted_role:
        await ctx.respond(f"Role '{junior_enlisted_role_name}' not found.")
        return

    if target:
        members_to_check = [member for member in target.members if junior_enlisted_role in member.roles]
    else:
        members_to_check = [member for member in ctx.guild.members if junior_enlisted_role in member.roles]

    no_squad_members = []
    for member in members_to_check:
        has_squad_role = any(squad_keyword.lower() in role.name.lower() for role in member.roles)
        if not has_squad_role:
            no_squad_members.append(member.mention)

    if no_squad_members:
        if target:
            await ctx.respond(f"JE without a 'Squad' role in {target}:\n" + "\n".join(no_squad_members))
        else:
            await ctx.respond(f"JE without a 'Squad' role in server:\n" + "\n".join(no_squad_members))
    else:
        await ctx.respond("All members have a 'Squad' role.")


def is_full_number(s):
    if not s:
        return False  # Empty string is not a number
    elif s[0] == '-':
        return s[1:].isdigit()  # Check if remaining characters are digits
    else:
        return s.isdigit()  # Check if all characters are digits


@bot.slash_command(name="deletecoin", description="Delete an invalid coin")
# @discord.default_permissions(administrator=True)
@option("target", description="Select the user to delete from")
async def deletecoin(ctx, target: discord.Member):
    if not check_permissions(ctx.author, ["Board of Admiralty"]) and not ctx.author.id == 713484585874227220:
        await ctx.respond("This command is restricted to BOA members only.", ephemeral=True)
        return

    commanders = []
    challenge = []

    try:
        with open("Coins.txt", "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []

    guild = ctx.guild

    for index, line in enumerate(lines):
        parts = line.strip().split(" - ")
        if len(parts) >= 4:
            member_id = parts[0]
            coin_type = parts[1]
            moderator_info = parts[2]
            timestamp = " - ".join(parts[4:])

            if int(member_id) == target.id:
                if moderator_info.isdigit():
                    moderator = guild.get_member(int(moderator_info))
                    if moderator:
                        moderator_display_name = moderator.display_name
                    else:
                        moderator_display_name = parts[3]
                else:
                    moderator_display_name = moderator_info

                if coin_type == "Commanders Challenge Coin":
                    commanders.append(f"{moderator_display_name}'s Commanders Challenge Coin (Line {index + 1})")
                elif coin_type == "Regular Challenge Coin":
                    challenge.append(f"{moderator_display_name}'s Challenge Coin (Line {index + 1})")

    if commanders:
        commanders_list = "\n".join(commanders)
    else:
        commanders_list = "None"

    if challenge:
        challenge_list = "\n".join(challenge)
    else:
        challenge_list = "None"

    embedVar = discord.Embed(title="Challenge Coins", color=0x00ff00)
    embedVar.add_field(name="Commander's Challenge Coins", value=commanders_list, inline=True)
    embedVar.add_field(name="Regular Challenge Coins", value=challenge_list, inline=True)

    editmessage = await ctx.respond(embed=embedVar)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
        content = msg.content.strip()

        if content.isdigit():
            line_number = int(content)

            with open("Coins.txt", "r") as file:
                lines = file.readlines()

            if 0 < line_number <= len(lines):
                with open("Coins.txt", "w") as file:
                    for index, line in enumerate(lines, start=1):
                        if index != line_number:
                            file.write(line)

                embedVar = discord.Embed(title="Challenge Coins", color=0x00ff00,
                                         description=f"Deleted challenge coin from line {line_number} from the database.")
                await editmessage.edit(embed=embedVar)
                return
            else:
                await ctx.send("Invalid line number. Please enter a valid line number.")
                return
        else:
            await ctx.send("Invalid input. Please respond with a valid line number to delete from Voyages.txt.")


    except asyncio.TimeoutError:
        embedVar = discord.Embed(title="Challenge Coins", color=0x00ff00, description="Timed out.")
        await editmessage.edit(embed=embedVar)
        return


@bot.slash_command(name="forceadd", description="Force-add voyages, subclasses, or other data to a user. (BOA ONLY!)")
# @discord.default_permissions(administrator=True)
@option("target", description="Select the user to forceadd data to")
@option("voyages", description="Add total voyages. Note: A user may need hosted voyages added seperately.")
@option("hosted", description="Add hosted voyages. Note: A user may need voyage count added seperately.")
@option("carpenter", description="Add carpenter subclass points")
@option("cannoneer", description="Add cannoneer subclass points")
@option("flex", description="Add flex subclass points")
@option("helm", description="Add helm subclass points")
@option("surgeon", description="Add field surgeon subclass points")
@option("grenadier", description="Add grenadier subclass points")
@option("coin", description="Add a coin to a member (REMEMBER TO DO COIN OWNER FIELD)", autocomplete=get_coin)
@option("coinowner", description="Add name of who gave the coin (REMEMBER TO DO COIN FIELD)")
async def forceadd(ctx, target: discord.Member, voyages=None, hosted=None, carpenter=None, cannoneer=None, flex=None,
                   helm=None, surgeon=None, grenadier=None, coin=None, coinowner=None):
    if not check_permissions(ctx.author, ["Board of Admiralty"]):
        await ctx.respond("This command is restricted to BOA members only.", ephemeral=True)
        return

    added = ""

    if voyages is not None:
        if is_full_number(voyages):
            log_forceadd(target.id, "Regular", voyages, ctx.author.id, datetime.utcnow())
            added += f"Voyages: {voyages}\n"
        else:
            added += f"Voyages were not added because the number was not an whole number."

    if hosted is not None:
        if is_full_number(hosted):
            log_forceadd(target.id, "Hosted", hosted, ctx.author.id, datetime.utcnow())
            added += f"Hosted: {hosted}\n"
        else:
            added += f"Hosted were not added because the number was not an whole number."

    if carpenter is not None:
        if is_full_number(carpenter):
            log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, "Carpenter", carpenter)
            added += f"Carpenter: {carpenter}\n"
        else:
            added += f"Carpenter were not added because the number was not an whole number."

    if cannoneer is not None:
        if is_full_number(cannoneer):
            log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, "Cannoneer", cannoneer)
            added += f"Cannoneer: {cannoneer}\n"
        else:
            added += f"Cannoneer were not added because the number was not an whole number."

    if flex is not None:
        if is_full_number(flex):
            log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, "Flex", flex)
            added += f"Flex: {flex}\n"
        else:
            added += f"Flex were not added because the number was not an whole number."

    if helm is not None:
        if is_full_number(helm):
            log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, "Helm", helm)
            added += f"Helm: {helm}\n"
        else:
            added += f"Helm were not added because the number was not an whole number."

    if surgeon is not None:
        if is_full_number(surgeon):
            log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, "Surgeon", surgeon)
            added += f"Surgeon: {surgeon}\n"
        else:
            added += f"Surgeon were not added because the number was not an whole number."

    if grenadier is not None:
        if is_full_number(grenadier):
            log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, "Grenadier", grenadier)
            added += f"Grenadier: {grenadier}\n"
        else:
            added += f"Grenadier was not added because the number was not an whole number."

    if coin and coinowner is not None:
        if coin == "Regular Challenge Coin":
            log_coin(target.id, "Regular Challenge Coin", "0", coinowner)
            added += f"Regular Coin: {coinowner}\n"

        elif coin == "Commanders Challenge Coin":
            log_coin(target.id, "Commanders Challenge Coin", "0", coinowner)
            added += f"Commanders Coin: {coinowner}\n"

        else:
            added += f"Please ensure you've added both a coin and coinowner. If it errors, try clicking the options for coin instead of typing.\n"

    await ctx.respond(f"Complete: \n{added}", ephemeral=True)


def get_user_stats(author_id):
    c.execute('SELECT * FROM people_data WHERE author_id = ?', (author_id,))
    row = c.fetchone()
    if row:
        stats = {
            "total_pings": row[1],
            "last_ping_time": row[2],
            "weekly_pings": row[3],
            "total_authored_messages": row[4],
            "last_authored_message_time": row[5],
            "weekly_authored_messages": row[6]
        }
        return stats
    else:
        return None


# Set up logging to see where it gets stuck
logging.basicConfig(level=logging.INFO, filename='bot.log', filemode='a',
                    format='%(asctime)s - %(levelname)s - %(message)s')

@bot.slash_command(name="member", description="Check information of a user or all users in a role")
@option("target", description="Choose a user or role to grab info for")
@option("level", description="Choose info view", autocomplete=get_levels)
async def member(ctx, target: discord.Member | discord.Role = None, level: str = None):
    logging.info(f"member command invoked by {ctx.author.display_name}")
    if target is None:
        target = ctx.author

    if level is None:
        level = "Default"

    if isinstance(target, discord.Role):
        members = target.members
        if level and level.lower() == "moderation":
            await ctx.respond("You can't use `moderation` on a role! Try again with a single person.")
            return
    else:
        members = [target]

    if len(members) >= 28:
        await ctx.respond("Too big of a role! Ship or smaller, please.")
        return

    # Defer the response to handle the request asynchronously
    try:
        await ctx.defer()
    except (discord.errors.NotFound, discord.errors.HTTPException) as e:
        logging.error(f"Failed to defer response for {ctx.author.display_name}: {e}")
        await ctx.respond("Failed to defer response. Please try again later.", ephemeral=True)
        return

    embed_messages = []

    async def process_member(member):
        try:
            embedVar = discord.Embed(title=member.display_name, description=f"<@{member.id}>", color=discord.Color.blue())

            if level.lower() == "default":
                time_in_server_field(embedVar, member)
                next_in_command_field(embedVar, ctx, member)
                await otherinfo_field(embedVar, member)
                logging.info(f"Processed other info for {member.display_name}")
                await voyage_field(embedVar, member)
                logging.info(f"Processed voyage field for {member.display_name}")
                await hosted_field(embedVar, member)
                logging.info(f"Processed hosted field for {member.display_name}")
                await titles_field(embedVar, member)
                await subclasses_field(embedVar, member)
                logging.info(f"Processed subclasses field for {member.display_name}")
                await coins_field(embedVar, member)
                embed_messages.append(embedVar)

            elif level.lower() == "moderation":
                if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer", "Senior Non Commissioned Officer",
                                                      "Non Commissioned Officer"]) and not ctx.author.id == 713484585874227220:
                    embedVar.add_field(name="Error",
                                       value="The arguments in this command are for Non-Commissioned Officers or higher. Please leave the field **Permissions** blank, or do a lower permission report.")
                    embed_messages.append(embedVar)
                    return

                valid_channel_ids = [1250615501898387557, 935688409920450630, 1101193993909456956, 1255693086957375538]
                if not ("bot-spam" in ctx.channel.name.lower() or ctx.channel.id in valid_channel_ids):
                    embedVar.add_field(name="Error",
                                       value="You can't do this in a public channel! Fleet bot spams or higher.")
                    embed_messages.append(embedVar)
                    return

                time_in_server_field(embedVar, member)
                next_in_command_field(embedVar, ctx, member)
                uservalue = str(member.id)
                embedVar.add_field(name="User ID", value=uservalue, inline=True)
                await subclasses_moderation_field(embedVar, member)

                if (check_permissions(ctx.author, ["Senior Officer", "Junior Officer",
                                                   "Senior Non Commissioned Officer"]) or ctx.author.id == 713484585874227220) and ctx.channel.id in valid_channel_ids:
                    await role_field(embedVar, member)
                    await name_field(embedVar, member)
                    await moderation_field(embedVar, member)
                    await notes_field(embedVar, member)
                else:
                    embedVar.set_footer(
                        text="If this view seems empty, Ensure you are sending the command in SNCO+ command channel.")
                embed_messages.append(embedVar)

            elif level.lower() == "promotion":
                await promotions_field(ctx, embedVar, member)
                embedVar.set_footer(text="Remember that data here may be inaccurate.")
                embed_messages.append(embedVar)

            else:
                embedVar.add_field(name="Error",
                                   value="The value you inputted into the `level` field is not a valid choice.")
                embed_messages.append(embedVar)

        except Exception as e:
            logging.error(f"Error processing member {member.display_name}: {e}")
            embedVar.add_field(name="Error", value=f"An error occurred while processing member {member.display_name}: {e}", inline=False)
            embed_messages.append(embedVar)

    try:
        await asyncio.gather(*[process_member(member) for member in members])
        logging.info(f"Processed members for {ctx.author.display_name}")
    except Exception as e:
        logging.error(f"Error processing members for {ctx.author.display_name}: {e}")
        await ctx.respond(f"An error occurred while processing members for {ctx.author.display_name}. Please try again later.", ephemeral=True)
        return

    for embed in embed_messages:
        try:
            await ctx.respond(embed=embed)
        except Exception as e:
            logging.error(f"Error responding with embed for {ctx.author.display_name}: {e}")
            await ctx.respond(f"An error occurred while sending the response for {ctx.author.display_name}. Please try again later.", ephemeral=True)
            return



@bot.slash_command(name="ping", description="Check if the bot is online")
async def ping(ctx):
    embedVar = discord.Embed(title="USN Hamtilities: Up and running!", color=discord.Color.blue())
    credits = "Owner and Creator: <@713484585874227220>\n Major coding help and bug fixer: <@690264788257079439>\nIdeas and BOA help: <@140988338432770058>\n"

    embedVar.add_field(name="Credits", value=credits, inline=True)
    await ctx.respond(f"Pong! We're up and running, sailor! Latency is {bot.latency}", embed=embedVar)


@bot.slash_command(name="removenote", description="Remove a moderation note from a user (SO+)")
# @discord.default_permissions(manage_channels=True)
@option("noteid", description="Write the number of the note to be removed")
async def removenote(ctx, noteid: int):
    if not check_permissions(ctx.author, ["Senior Officer"]) and not ctx.author.id == 713484585874227220:
        await ctx.defer(ephemeral=True)
        await ctx.followup.send(
            "This command is only available for Senior Officers or higher.")
        return

    try:
        with open("ModNotes.txt", "r") as file:
            lines = file.readlines()

        with open("ModNotes.txt", "w") as file:
            removed = False
            for index, line in enumerate(lines, start=1):
                if index != noteid:
                    file.write(line)
                else:
                    removed = True

            if removed:
                await ctx.respond(f"Note with ID {noteid} has been removed.")
            else:
                await ctx.respond("Note not found with the provided ID.")

    except FileNotFoundError:
        await ctx.send("ModNotes.txt file not found.")


@bot.slash_command(name="searchgt", description="Get members username by gamertag")
# @discord.default_permissions(manage_messages=True)
@option("gamertag", description="User to search for by gamertag")
async def searchgt(ctx, gamertag):
    if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer",
                                          "Senior Non Commissioned Officer"]) or ctx.author.id == 713484585874227220:
        await ctx.respond("This command is for SNCO+!", ephemeral=True)
        return

    with open("Gamertags.txt", "r") as gt_file:
        lines = gt_file.readlines()

    user_gamertags = {}
    for line in lines:
        user_id, gt = line.strip().split(" - ", 1)
        if user_id not in user_gamertags:
            user_gamertags[user_id] = gt
        else:
            user_gamertags[user_id] = gt

    lines.reverse()
    for line in lines:
        user_id, gt = line.strip().split(" - ", 1)
        if gt == gamertag:
            if user_gamertags[user_id] == gt:
                gamertag_info = f"User: <@{user_id}>, GT: {gt}"
                member = await ctx.guild.fetch_member(user_id)
                if not check_permissions(member, ["Junior Enlisted", "Non Commissioned Officer,",
                                                  "Senior Non Commissioned Officer", "Junior Officer",
                                                  "Senior Officer"]):
                    if check_permissions(ctx.author, ["Board of Admiralty"]) and check_permissions(member,
                                                                                                   ["Junior Enlisted",
                                                                                                    "Non Commissioned Officer,",
                                                                                                    "Senior Non Commissioned Officer",
                                                                                                    "Junior Officer",
                                                                                                    "Senior Officer",
                                                                                                    "Deckhand | W-1",
                                                                                                    "Civilian",
                                                                                                    "Retired",
                                                                                                    "Veteran",
                                                                                                    "Ambassador"]):
                        await ctx.respond(f"User: <@{user_id}>, GT: {gt}", ephemeral=True)
                        return
                    else:
                        await ctx.respond(gamertag_info, ephemeral=True)
                        return
                await ctx.respond(gamertag_info, ephemeral=True)
            else:
                await ctx.respond(f"User not found for gamertag `{gamertag}`.", ephemeral=True)
            break
    else:
        await ctx.respond(f"User not found for gamertag `{gamertag}`.", ephemeral=True)


async def check_testing(ctx):
    if ctx.guild.id == 933907909954371654:
        if check_permissions(ctx.author, [
            "Board of Admiralty"]) or ctx.author.id == 713484585874227220 or ctx.author.id == 690264788257079439:
            return True
        else:
            return False
    return True


def get_time_difference_future(other_time):
    if other_time.tzinfo is None or other_time.tzinfo.utcoffset(other_time) is None:
        other_time = other_time.replace(tzinfo=datetime.timezone.utc)

    current_time = datetime.now(timezone.utc)
    time_difference = other_time - current_time
    return time_difference


def get_time_difference_past(other_time):
    if other_time is None:
        return

    if other_time.tzinfo is None or other_time.utcoffset() is None:
        other_time = other_time.replace(tzinfo=timezone.utc)

    current_time = datetime.now(timezone.utc)
    time_difference = current_time - other_time
    return time_difference


def format_time(time_difference):
    years = time_difference.days // 365
    months = (time_difference.days % 365) // 30
    weeks = (time_difference.days % 365 % 30) // 7
    days = time_difference.days % 365 % 30 % 7
    hours = time_difference.seconds // 3600
    minutes = (time_difference.seconds % 3600) // 60
    seconds = time_difference.seconds % 60

    if years >= 1:
        return f"{years} year{'s' if years > 1 else ''}" + (
            f", {months} month{'s' if months > 1 else ''}" if months > 0 else "")
    elif months >= 1:
        return f"{months} month{'s' if months > 1 else ''}" + (
            f", {weeks} week{'s' if weeks > 1 else ''}" if weeks > 0 else "")
    elif weeks >= 1:
        return f"{weeks} week{'s' if weeks > 1 else ''}" + (
            f", {days} day{'s' if days > 1 else ''}" if days > 0 else "")
    elif days >= 1:
        return f"{days} day{'s' if days > 1 else ''}" + (
            f", {hours} hour{'s' if hours > 1 else ''}" if hours > 0 else "")
    elif hours >= 1:
        return f"{hours} hour{'s' if hours > 1 else ''}" + (
            f", {minutes} minute{'s' if minutes > 1 else ''}" if minutes > 0 else "")
    elif minutes >= 1:
        return f"{minutes} minute{'s' if minutes > 1 else ''}" + (
            f", {seconds} second{'s' if seconds > 1 else ''}" if seconds > 0 else "")
    else:
        return "Just Now"


# https://discord.com/oauth2/authorize?client_id=1145532919666987149&permissions=8&scope=bot+applications.commands


async def add_note_to_file(target_id, moderator_id, note):
    with open("ModNotes.txt", "a") as file:
        file.write(f"{target_id} - {moderator_id} - {note}\n")


async def log_event(event):
    with open("Auditlogs.txt", "a") as f:
        f.write(f"{event}\n")


def log_subclasses(author_id, log_link, target_id, subclass, count):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with open("Subclasses.txt", "a") as file:
        file.write(f"{author_id} - {log_link} - {target_id} - {subclass} - {count} - {timestamp}\n")


def log_voyage(member_id, action, num_change, moderator):
    with open("Voyages.txt", "a") as file:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{member_id} - {action} - {num_change} - {moderator} - {timestamp}\n")


def log_coin(member_id, type, moderator, old_name):
    with open("Coins.txt", "a") as file:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        file.write(f"{member_id} - {type} - {moderator} - {old_name} - {timestamp}\n")


async def confirm_send(ctx, message=str):
    confirmation_message = await ctx.respond(message)

    def check(message):
        return message.author == ctx.author and message.channel == ctx.channel and message.content.lower() in [
            'confirm', 'cancel']

    try:
        user_response = await bot.wait_for('message', check=check, timeout=60.0)
        if user_response.content.lower() == 'confirm':
            await confirmation_message.delete()
            await user_response.delete()
            return True
        else:
            await confirmation_message.delete()
            await user_response.delete()
            return False
    except asyncio.TimeoutError:
        await ctx.send("Confirmation timed out. Command canceled.")
        try:
            await confirmation_message.delete()
            await user_response.delete()
        except Exception as e:
            print(f"Failed to delete confirmation message: {e}")
        return False


def check_permissions(member: discord.Member, required_roles):
    for role in member.roles:
        if role.name in required_roles:
            return True
    return False


def get_role_in_list(member, role_list):
    for role in member.roles:
        if role.name in role_list:
            return role
    return None


def get_role_with_keyword(member, keyword):
    roles_with_keyword = [role for role in member.roles if keyword.lower() in role.name.lower()]
    if roles_with_keyword:
        return roles_with_keyword[0]
    return None


def loa2_check(ctx, id, index):
    if "LOA-2" in id.display_name:
        nextCO = process_role_index(ctx, id, index)
        return nextCO
    return True


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
            break

    if highest_ranking_role is None:
        return None

    for index, role_name in enumerate(listidentify):
        if highest_ranking_role.name == role_name:
            return index
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


async def get_voyage_info(member):
    return count_voyages(member.id, "Voyages")


async def get_hosted_info(member):
    return count_voyages(member.id, "Hosted")


def count_voyages(member_id, action):
    total_count = 0
    latest_timestamp = None
    last_month_count = 0
    one_month_ago = datetime.now(timezone.utc) - timedelta(days=30)

    if action == "Hosted":
        file_path = "Hosted.txt"
    else:
        action = "Regular"
        file_path = "Voyages.txt"

    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(" - ")
            if len(parts) >= 4:
                log_id, member, change, time = parts
                file_member_id = int(member)
                timestamp = datetime.fromisoformat(time)

                if file_member_id == member_id:
                    total_count += int(change)
                    latest_timestamp = timestamp
                    if timestamp >= one_month_ago:
                        last_month_count += int(change)

        weekly_voyages = last_month_count / 4

    with open("Forceadd.txt", "r") as file:
        for line in file:
            parts = line.strip().split(" - ")
            if len(parts) >= 4:
                member, type, count, moderator, time = parts
                member = int(member)
                if member == member_id and type == action:
                    print("YEEEE HAW")
                    total_count += int(count)

    return [latest_timestamp, weekly_voyages, total_count]


async def role_changes(member_id):
    changes = []
    with open("Auditlogs.txt", "r") as f:
        lines = f.readlines()
        lines.reverse()
        count = 0
        for line in lines:
            parts = line.strip().split(" - ")
            if parts[0].strip() == str(member_id).strip():
                action_type = parts[1]
                if action_type in ["Role Added", "Role Removed"]:
                    if action_type == "Role Added":
                        role = parts[2]
                        moderator = parts[3]
                        action_time = datetime.strptime(parts[4], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))

                        changes.append(f"<@&{role}> added by <@{moderator}> ({time_diff})")
                    elif action_type == "Role Removed":
                        role = parts[2]
                        moderator = parts[3]
                        action_time = datetime.strptime(parts[4], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))
                        changes.append(f"<@&{role}> removed by <@{moderator}> ({time_diff})")

                    count += 1
                    if count == 5:
                        break

    if count == 0:
        return "No role changes"
    return "\n".join(changes)


async def name_changes(member_id):
    changes = []
    with open("Auditlogs.txt", "r") as f:
        lines = f.readlines()
        lines.reverse()
        count = 0
        for line in lines:
            parts = line.strip().split(" - ")
            if parts[0].strip() == str(member_id).strip():
                action_type = parts[1]
                if action_type == "Nickname Change":
                    before = parts[2]
                    after = parts[3]
                    moderator = parts[4]
                    action_time = datetime.strptime(parts[5], "%Y-%m-%d %H:%M:%S.%f").replace(
                        tzinfo=timezone.utc)  # Correct usage of timezone.utc
                    # Time of nickname change in UTC
                    time_diff = format_time(get_time_difference_past(action_time))
                    changes.append(f"`{before}` to `{after}` by <@{moderator}> ({time_diff})")
                    count += 1
                    if count == 5:
                        break
    return "\n".join(changes)


async def tiered_medals(member):
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

    categories = [
        ("Hosting Titles", hosting_titles),
        ("Voyaging Titles", voyaging_titles),
        ("Combat Titles", combat_titles),
        ("Conduct Titles", conduct_titles),
        ("Time Titles", time_titles),
        ("Training Titles", training_titles),
    ]

    result = ""

    for category_name, titles in categories:
        for role in member.roles:
            if role.name in titles:
                result += f"<@&{role.id}>\n"
                break

    return result


async def other_medals(member):
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
        "Commanders Challenge Coin",
        "Challenge Coin",
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


async def mod_actions(member_id):
    moderation_actions = []
    with open("Auditlogs.txt", "r") as f:
        lines = f.readlines()
        lines.reverse()
        count = 0
        for line in lines:
            parts = line.strip().split(" - ")
            if parts[0] == member_id:
                action_type = parts[1]
                if action_type in ["Timed Out", "Untimed Out", "Member Left", "Member Banned", "Member Unbanned",
                                   "Member Kicked"] and count < 5:
                    if action_type == "Member Left":
                        action_time = datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=datetime.timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))
                        moderation_actions.append((f"**Left** on", time_diff))
                    elif action_type == "Timed Out":
                        timeout_duration = parts[2]
                        moderator = parts[3]
                        action_time = datetime.strptime(parts[4], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=datetime.timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))
                        moderation_actions.append(
                            (f"**Timed out** for {timeout_duration} by <@{moderator}>", time_diff))
                    elif action_type == "Untimed Out":
                        moderator = parts[2]
                        action_time = datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=datetime.timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))
                        moderation_actions.append((f"**Untimed out** by <@{moderator}>", time_diff))
                    elif action_type == "Member Banned":
                        moderator = parts[2]
                        action_time = datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=datetime.timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))
                        moderation_actions.append((f"**Banned** by <@{moderator}>", time_diff))
                    elif action_type == "Member Unbanned":
                        moderator = parts[2]
                        action_time = datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=datetime.timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))
                        moderation_actions.append((f"**Unbanned** by <@{moderator}>", time_diff))
                    elif action_type == "Member Kicked":
                        moderator = parts[2]
                        action_time = datetime.strptime(parts[3], "%Y-%m-%d %H:%M:%S.%f").replace(
                            tzinfo=datetime.timezone.utc)
                        time_diff = format_time(get_time_difference_past(action_time))
                        moderation_actions.append((f"**Kicked** by <@{moderator}>", time_diff))
                    count += 1
                if count >= 5:
                    break
    return moderation_actions


async def count_messages(member, category, days):
    date_limit = datetime.now(timezone.utc) - timedelta(days=days)
    messages_count = 0

    if category == "Voyages":
        file_path = "Voyages.txt"
    elif category == "Hosted":
        file_path = "Hosted.txt"
    else:
        raise ValueError("Invalid category. Must be 'Voyages' or 'Hosted'.")

    with open(file_path, "r") as file:
        for line in file:
            parts = line.strip().split(" - ")
            if len(parts) >= 4:
                _, member_id, change, timestamp_str = parts
                file_member_id = int(member_id)
                timestamp = datetime.fromisoformat(timestamp_str)

                if file_member_id == member.id and timestamp >= date_limit:
                    messages_count += int(change)

    return messages_count


def assign_time(member_id, role_id):
    with open("Auditlogs.txt", "r") as f:
        lines = f.readlines()
        lines.reverse()

        for line in lines:
            parts = line.strip().split(" - ")
            if parts[0].strip() == str(member_id).strip() and parts[1].strip() == "Role Added" and parts[
                2].strip() == role_id:
                return parts[4].strip()

    return None


def str_to_datetime(time_str):
    try:
        # Try parsing with fractional seconds
        time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        # If parsing fails, try without fractional seconds
        time = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

    time = time.replace(tzinfo=timezone.utc)
    return time


async def otherinfo_field(embedVar, member):
    target_id = str(member.id)
    gamertag_info = "No Gamertag"
    timezone_info = "No Timezone"

    with open("Gamertags.txt", "r") as gt_file:
        lines = gt_file.readlines()
        lines.reverse()
        for line in lines:
            if line.startswith(target_id):
                _, gamertag = line.strip().split(" - ", 1)
                gamertag_info = f"GT: {gamertag}"
                break

    with open("Timezones.txt", "r") as tz_file:
        lines = tz_file.readlines()
        for line in lines:
            if line.startswith(target_id):
                _, timezone = line.strip().split(" - ", 1)
                timezone_info = f"TZ: {timezone}"
                break

    info = f"{gamertag_info}\n{timezone_info}"
    embedVar.add_field(name="Other Info", value=info, inline=True)


def time_in_server_field(embedVar, member):
    joined_at_str = str(member.joined_at)
    joined_at = datetime.strptime(joined_at_str, "%Y-%m-%d %H:%M:%S.%f%z")
    totaltime = format_time(get_time_difference_past(joined_at))
    embedVar.add_field(name="Time in Server", value=totaltime, inline=True)


def next_in_command_field(embedVar, ctx, member):
    role_index = identify_role_index(ctx, member)

    nextincommand_result = process_role_index(ctx, member, role_index)

    if len(nextincommand_result) == 1:
        if nextincommand_result is None or not isinstance(nextincommand_result, list):
            embedVar.add_field(name="Next in Command", value=nextincommand_result, inline=True)
        else:
            nextincommand_result = nextincommand_result[0]
            embedVar.add_field(name="Next in Command", value=f"<@{nextincommand_result}>", inline=True)
    elif len(nextincommand_result) == 2:
        current_member_id = str(nextincommand_result[1])[1:-1]
        current_member_mention = f"<@{current_member_id}>"
        immediate_member_id = nextincommand_result[0]
        immediate_member_mention = f"<@{immediate_member_id}>"
        embedVar.add_field(name="Next in Command",
                           value=f"Current: {current_member_mention}\n Immediate: {immediate_member_mention}",
                           inline=True)
    else:
        embedVar.add_field(name="Next in Command", value=f"Unknown", inline=True)


async def coins_field(embedVar, member):
    commanders = []
    challenge = []

    try:
        with open("Coins.txt", "r") as file:
            lines = file.readlines()
    except FileNotFoundError:
        lines = []

    guild = member.guild

    for line in lines:
        parts = line.strip().split(" - ")
        if len(parts) >= 4:
            member_id = parts[0]
            coin_type = parts[1]
            moderator_info = parts[2]
            timestamp = " - ".join(parts[4:])  # Join the remaining parts to handle the timestamp

            if int(member_id) == member.id:
                if moderator_info.isdigit():  # Check if the moderator info is an ID
                    moderator = guild.get_member(int(moderator_info))
                    if moderator:
                        moderator_display_name = moderator.display_name
                    else:
                        moderator_display_name = parts[3]
                else:
                    moderator_display_name = moderator_info  # Set moderator display name as the provided info

                if coin_type == "Commanders Challenge Coin":
                    commanders.append(f"{moderator_display_name}'s Commanders Challenge Coin")
                elif coin_type == "Regular Challenge Coin":
                    challenge.append(f"{moderator_display_name}'s Challenge Coin")

    embedVar.add_field(name="Commander's Challenge Coins", value="\n".join(commanders) if commanders else "None",
                       inline=True)
    embedVar.add_field(name="Regular Challenge Coins", value="\n".join(challenge) if challenge else "None", inline=True)


async def voyage_field(embedVar, member):
    try:
        voyage_info = await get_voyage_info(member)
        last_voyage = get_time_difference_past(voyage_info[0])
        if last_voyage == None:
            last_voyaged = None
        else:
            last_voyage_format = format_time(last_voyage)
            if last_voyage.days >= 30:
                last_voyaged = ":x: " + last_voyage_format
            else:
                last_voyaged = ":white_check_mark: " + last_voyage_format

        embedVar.add_field(name="Last Voyage", value=last_voyaged, inline=True)
        embedVar.add_field(name="Average Weekly Voyages", value=round(voyage_info[1], 2), inline=True)
        embedVar.add_field(name="Total Voyages", value=voyage_info[2], inline=True)

    except Exception as e:
        embedVar.add_field(name="Last Voyage", value="Error occurred", inline=True)
        embedVar.add_field(name="Average Weekly Voyages", value="Error occurred", inline=True)
        embedVar.add_field(name="Total Voyages", value="Error occurred", inline=True)
        print(e)


async def hosted_field(embedVar, member):
    try:
        voyage_info = await get_hosted_info(member)

        if voyage_info[2] == 0:
            return

        last_hosted = get_time_difference_past(voyage_info[0])
        last_hosted_format = format_time(last_hosted)

        if last_hosted.days >= 14:
            last_hosted_display = ":x: " + last_hosted_format
        else:
            last_hosted_display = ":white_check_mark: " + last_hosted_format

        embedVar.add_field(name="Last Hosted", value=last_hosted_display, inline=True)
        embedVar.add_field(name="Average Weekly Hosted", value=round(voyage_info[1], 2), inline=True)
        embedVar.add_field(name="Total Hosted", value=voyage_info[2], inline=True)

    except Exception as e:
        embedVar.add_field(name="Last Hosted", value="Error occurred", inline=True)
        embedVar.add_field(name="Average Weekly Hosted", value="Error occurred", inline=True)
        embedVar.add_field(name="Total Hosted", value="Error occurred", inline=True)
        print(e)


async def role_field(embedVar, member):
    role_output = await role_changes(member.id)

    embedVar.add_field(name="Role Changes", value=role_output, inline=False)


async def name_field(embedVar, member):
    name_output = await name_changes(member.id)

    if name_output and not name_output == []:
        embedVar.add_field(name="Name Changes", value=name_output, inline=False)
    else:
        embedVar.add_field(name="Name Changes", value="No name changes", inline=False)


async def titles_field(embedVar, member):
    tiered_output = await tiered_medals(member)

    if tiered_output != "":
        embedVar.add_field(name="Tiered Awards", value=tiered_output, inline=True)
    else:
        embedVar.add_field(name="Tiered Awards", value="None", inline=True)

    medals_output = await other_medals(member)
    if medals_output != []:
        formatted = "\n".join(medals_output)
        embedVar.add_field(name="Awards / Titles", value=formatted, inline=True)
    else:
        embedVar.add_field(name="Awards / Titles", value="None", inline=True)


async def subclasses_moderation_field(embedVar, member):
    with open("Subclasses.txt", "r") as file:
        lines = file.readlines()

    entries_found = 0
    subclass_entries = []

    for line_number, line in enumerate(reversed(lines), start=1):
        parts = line.strip().split(" - ")
        if len(parts) >= 6 and parts[2] == str(member.id):
            if entries_found >= 5:
                break
            if parts[1] != "BOA OVERRIDE":
                moderator_id = parts[0]
                try:
                    timestamp = datetime.strptime(parts[5], "%Y-%m-%d %H:%M:%S")
                    time_difference = format_time(get_time_difference_past(timestamp))
                except ValueError:
                    time_difference = "Unknown"
                subclass = parts[3]
                points = int(parts[4])
                role_mention = f"<@{moderator_id}>"
                subclass_entries.append(
                    f"{role_mention}: {subclass} - {points} ({time_difference} ago)")
                entries_found += 1

    if subclass_entries:
        subclass_str = "\n".join(subclass_entries)
        subclass_str = subclass_str + "\n`If there are errors, redo the /addsubclass command on the log.`"
        embedVar.add_field(name="Subclass Moderation History", value=subclass_str, inline=False)
    else:
        embedVar.add_field(name="Subclass Moderation History", value="No subclass moderation history found",
                           inline=False)


async def moderation_field(embedVar, member):
    mod_actions_list = await mod_actions(str(member.id))

    if mod_actions_list and not mod_actions_list == []:
        embedVar.add_field(name="Moderations",
                           value="\n".join([f"{action[0]} ({action[1]})" for action in mod_actions_list]))
    else:
        embedVar.add_field(name="Moderations", value="No moderations here")


async def notes_field(embedVar, member):
    try:
        with open("ModNotes.txt", "r") as file:
            all_notes = []

            for line_number, line in enumerate(file, start=1):
                parts = line.strip().split(" - ")
                if len(parts) >= 3 and parts[0] == str(member.id):
                    moderator_id = parts[1]
                    note = "-".join(parts[2:])
                    all_notes.append(f"<@{moderator_id}>: {note} (Case `{line_number}`)\n")

            recent_notes = all_notes[-5:]
            recent_notes.reverse()
            notes_str = ''.join(recent_notes)

            if notes_str:
                embedVar.add_field(name="Moderator Notes", value=notes_str, inline=False)
            else:
                embedVar.add_field(name="Moderator Notes", value="No moderation notes found", inline=False)

    except FileNotFoundError:
        embedVar.add_field(name="Moderator Notes", value="ModNotes.txt file not found", inline=False)


async def promotions_field(ctx, embedVar, member):
    channel_id = 935343526626078850
    channel = bot.get_channel(channel_id)
    roles = [
        # BOA
        "Admiral | O-10",
        "Vice Admiral | O-9",
        "Rear Admiral | O-8",
        "Commodore | O-7",
        "Master Chief petty Officer of the Navy",

        # SO and JO
        "Captain | O-6",
        "Commander | O-5",
        "Lieutenant Commander | O-4",
        "Lieutenant | O-3",
        "Midshipman | O-1",

        # SNCO and NCO
        "Senior Chief Petty Officer | E-8",
        "Chief Petty Officer | E-7",
        "Petty Officer | E-6",
        "Junior Petty Officer | E-4",

        # JE
        "Able Seaman | E-3",
        "Seaman | E-2",
        "Seaman Apprentice | W-2"
    ]

    found_role = None

    for role in member.roles:
        if role.name in roles:
            found_role = role.name
            break

    if found_role in roles:
        if found_role == "Seaman Apprentice | W-2":
            role_assign_time = assign_time(member.id, "1201933589357547540")
            if role_assign_time:
                role_assign_time = str_to_datetime(role_assign_time)
                messages_since_role_assign = await count_messages(member, "Voyages", role_assign_time.days)

                if messages_since_role_assign >= 1:
                    send = f":white_check_mark: Go on one voyage since becoming W-2: ({messages_since_role_assign}/1)"
                else:
                    send = f":x: Go on one voyage since becoming W-2: ({messages_since_role_assign}/1)"
            else:
                send = ":x: Go on one voyage since becoming W-2: (Unknown/1)"
            embedVar.add_field(name="Promotion Requirements", value=send, inline=False)

        elif found_role == "Seaman | E-2":
            role_assign_time = assign_time(member.id, "933913010806857801")
            if role_assign_time:
                role_assign_time = str_to_datetime(role_assign_time)
                messages_since_role_assign = await count_messages(member, "Voyages", role_assign_time.days)

                if messages_since_role_assign >= 5:
                    promotion_requirement = f":white_check_mark: Go on five voyages: ({messages_since_role_assign}/5)"
                else:
                    promotion_requirement = f":x: Go on five voyages: ({messages_since_role_assign}/5)"

            else:
                promotion_requirement = ":x: Go on five voyages: (Unknown/5)"

            citation_roles = ["Citation of Conduct", "Legion of Conduct", "Honorable Conduct Medal",
                              "Meritorious Conduct Medal", "Admirable Conduct Medal", "Citation Of Combat",
                              "Legion of Combat", "Honorable Combat Action", "Meritorious Combat Action",
                              "Admirable Combat Action"]
            citation_role = next((role.name for role in member.roles if role.name in citation_roles), None)
            last_word = ' '.join(citation_role.split()[-1:]) if citation_role else None

            if citation_role:
                promotion_requirement += f"\n:white_check_mark: <@&944648745503563806> or <@&944648920083079189> ({last_word})"
            else:
                promotion_requirement += "\n:x: Holds <@&944648745503563806> or <@&944648920083079189>"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements", value="Decent activity in squad chat", inline=False)

        elif found_role == "Able Seaman | E-3":
            role_assign_time = assign_time(member.id, "1231710098234015815")
            if role_assign_time is not None:
                test = str_to_datetime(role_assign_time)
                messages_since_role_assign = await count_messages(member, "Voyages", role_assign_time.days)

                role_since = format_time(get_time_difference_past(test))

                async for message in message_history:
                    if message.created_at > test:
                        if len(message.mentions) >= 1 and member in message.mentions:
                            messages_since_role_assign += 1

                current_time = datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                time_difference = current_time - test

                if time_difference.days >= 14:
                    if messages_since_role_assign >= 15:
                        one = f"- :white_check_mark: Go on 15 voyages ({messages_since_role_assign}/15) and two weeks as an E-3 ({role_since})"
                    else:
                        one = f"- :x: Go on 15 voyages ({messages_since_role_assign}/15) and two weeks as an E-3 ({role_since})"
                else:
                    one = f"- :x: Go on 15 voyages ({messages_since_role_assign}/15) and two weeks as an E-3 ({role_since})"

                if time_difference.days >= 7:
                    if messages_since_role_assign >= 20:
                        two = f"\n- :white_check_mark: Go on 20 voyages ({messages_since_role_assign}/20) and one week as an E-3 ({role_since})"
                    else:
                        two = f"\n- :x: Go on 20 voyages ({messages_since_role_assign}/20) and one week as an E-3 ({role_since})"
                else:
                    two = f"\n- :x: Go on 20 voyages ({messages_since_role_assign}/20) and one week as an E-3 ({role_since})"

                promotion_requirement = one + f"\n**OR**" + two


            else:
                one = f"- :x: Go on 15 voyages (Unknown/15) and two weeks as an E-3 (Unknown)"
                two = f"\n- :x: Go on 20 voyages (Unknown/20) and one week as an E-3 (Unknown)"
                promotion_requirement = one + f"\n**OR**" + two

            citation_role_present = any(role.name == "Citation of Conduct" for role in member.roles)

            if citation_role_present == True:
                promotion_requirement += f"\n\n:white_check_mark: Has Citation of Conduct"
            else:
                promotion_requirement += f"\n\n:x: Has Citation of Conduct"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements", value="Complete JLA", inline=False)

        elif found_role == "Junior Petty Officer | E-4":
            spd_departments = ["NRC Department", "Logistics Department", "Scheduling Department", "Media Department",
                               "NETC Department"]
            spd_role = next((role.name for role in member.roles if role.name in spd_departments), None)

            if spd_role:
                promotion_requirement = f":white_check_mark: Join an SPD Department ({spd_role})"
            else:
                promotion_requirement = ":x: Join an SPD Department"

            role_present = any(role.name == "NCO Improvement Ribbon" for role in member.roles)

            if role_present == True:
                promotion_requirement += f"\n:white_check_mark: Have NCO Improvement Ribbon"
            else:
                promotion_requirement += f"\n:x: Have NCO Improvement Ribbon"

            hosted_info = await get_hosted_info(member)
            voyages_hosted = hosted_info[2]

            if voyages_hosted >= 10:
                promotion_requirement += f"\n:white_check_mark: Host 10 official voyages ({voyages_hosted}/10)"
            else:
                promotion_requirement += f"\n:x: Host 10 official voyages ({voyages_hosted}/10)"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements",
                               value="Apply for position of XO to a squad or become a squad leader (when available)",
                               inline=False)

        elif found_role == "Admiral of the Navy":
            embedVar.add_field(name="This role is too high!",
                               value="This role may be personally picked by the AOTN, or may not have a rankup.",
                               inline=False)

        elif found_role == "Vice Admiral of the Navy":
            embedVar.add_field(name="This role is too high!",
                               value="This role may be personally picked by the AOTN, or may not have a rankup.",
                               inline=False)

        elif found_role == "Rear Admiral | O-8":
            embedVar.add_field(name="This role is too high!",
                               value="This role may be personally picked by the AOTN, or may not have a rankup.",
                               inline=False)

        elif found_role == "Commodore | O-7":
            embedVar.add_field(name="This role is too high!",
                               value="This role may be personally picked by the AOTN, or may not have a rankup.",
                               inline=False)

        elif found_role == "Captain | O-6":
            embedVar.add_field(name="This role is too high!",
                               value="This role may be personally picked by the AOTN, or may not have a rankup.",
                               inline=False)

        elif found_role == "Commander | O-5":
            role_assign_time = assign_time(member.id, "1231710098301259842")
            if role_assign_time:
                test = str_to_datetime(role_assign_time)

                current_time = datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                time_difference = current_time - test
                if time_difference.days >= 60:
                    promotion_requirement = f":white_check_mark: 2 months (60 days) spent as O-5 ({time_difference.days}/60)"
                else:
                    promotion_requirement = f":x: 2 months (60 days) spent as O-5 ({time_difference.days}/60)"
            else:
                promotion_requirement = f":x: 2 months (60 days) spent as O-5 (Unknown/60)"

            role_present = any(role.name == "Maritime Service Medal" for role in member.roles)

            if role_present == True:
                promotion_requirement += f"\n:white_check_mark: Have Maritime Service Medal"
            else:
                promotion_requirement += f"\n:x: Have Maritime Service Medal"

            additional_requirement = "Very Active Ship" + "\nFull CoC on ship (CoS optional)"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements", value=additional_requirement, inline=False)

        elif found_role == "Lieutenant Commander | O-4":
            role_assign_time = assign_time(member.id, "1231710098301259840")
            if role_assign_time:
                test = str_to_datetime(role_assign_time)

                current_time = datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                time_difference = current_time - test

                if time_difference.days >= 21:
                    promotion_requirement = f":white_check_mark: 21 days spent as O-4 ({time_difference.days}/21)"
                else:
                    promotion_requirement = f":x: 21 days spent as O-4 ({time_difference.days}/21)"
            else:
                promotion_requirement = f":x: 21 days spent as O-4 (Unknown/21)"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements",
                               value="Functional CoC on your ship (Fulfills all duties even if incomplete) \nRecruit and maintain 12 members from outside the server on your ship, not including CO/XO/CoS",
                               inline=False)

        elif found_role == "Lieutenant | O-3":
            additional_requirement = "Complete SOCS" + "\nVoted on by BOA"
            embedVar.add_field(name="Additional Requirements", value=additional_requirement, inline=False)

        elif found_role == "Midshipman | O-1":
            role_assign_time = assign_time(member.id, "1231710098250797061")
            if role_assign_time:
                test = str_to_datetime(role_assign_time)

                current_time = datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
                time_difference = current_time - test

                if time_difference.days >= 14:
                    promotion_requirement = f":white_check_mark: 14 days spent as O-1 ({time_difference.days}/14)"
                else:
                    promotion_requirement = f":x: 14 days spent as O-1 ({time_difference.days}/14)"
            else:
                promotion_requirement = f":x: 14 days spent as O-1 (Unknown/14)"

            additional_requirement = "Complete OCS" + "\nMentorship Under SO"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements", value=additional_requirement, inline=False)

        elif found_role == "Master Chief Petty Officer of the Navy":
            embedVar.add_field(name="This role is too high!",
                               value="This role may be personally picked by the AOTN, or may not have a rankup.",
                               inline=False)

        elif found_role == "Senior Chief Petty Officer | E-8":
            embedVar.add_field(name="Note:",
                               value="This is the highest normally obtainable SNCO rank, and can signify that this user has chosen to stay as an Enlisted Leader.",
                               inline=False)

            hosted_info = await get_hosted_info(member)
            voyages_hosted = hosted_info[2]

            if voyages_hosted >= 35:
                promotion_requirement = f"\n:white_check_mark: Host 35 official voyages ({voyages_hosted}/35)"
            else:
                promotion_requirement = f"\n:x: Host 35 official voyages ({voyages_hosted}/35)"

            conduct_roles = ["Honorable Conduct Medal", "Meritorious Conduct Medal", "Admirable Conduct Medal"]
            conduct_role = next((role.name for role in member.roles if role.name in conduct_roles), None)

            time_roles = ["4 Months Service Stripes", "6 Months Service Stripes", "8 Months Service Stripes",
                          "12 Months Service Stripes", "18 Months Service Stripes", "24 Month Service Stripes"]
            time_role = next((role.name for role in member.roles if role.name in time_roles), None)

            if conduct_role:
                promotion_requirement += f"\n:white_check_mark: Honorable Conduct Medal ({conduct_role})"
            else:
                promotion_requirement += f"\n:x: Honorable Conduct Medal ({conduct_role})"

            if time_role:
                promotion_requirement += f"\n:white_check_mark: 4 Month Service Stripes ({time_role})"
            else:
                promotion_requirement += f"\n:x: 4 Month Service Stripes ({time_role})"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements", value="Officer Board", inline=False)

        elif found_role == "Chief Petty Officer | E-7":
            confirmation = await ctx.send(
                "This requires a route, as E-8 and O-1 are both possible options. Please send `E-8` or `O-1`, or `cancel` to stop.")

            try:
                message = await ctx.bot.wait_for(
                    'message',
                    timeout=20.0,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel and m.content in ["E-8", "O-1",
                                                                                                          "cancel"]
                )
            except asyncio.TimeoutError:
                await ctx.send("Cancelled")
            else:
                if message.content == "E-8":
                    await confirmation.delete()
                    conduct_roles = ["Honorable Conduct Medal", "Meritorious Conduct Medal", "Admirable Conduct Medal"]
                    conduct_role = next((role.name for role in member.roles if role.name in conduct_roles), None)

                    time_roles = ["4 Months Service Stripes", "6 Months Service Stripes", "8 Months Service Stripes",
                                  "12 Months Service Stripes", "18 Months Service Stripes", "24 Months Service Stripes"]
                    time_role = next((role.name for role in member.roles if role.name in time_roles), None)

                    if conduct_role:
                        promotion_requirement = f"\n:white_check_mark: Honorable Conduct Medal ({conduct_role})"
                    else:
                        promotion_requirement = f"\n:x: Honorable Conduct Medal ({conduct_role})"

                    if time_role:
                        promotion_requirement += f"\n:white_check_mark: 4 Month Service Stripes ({time_role})"
                    else:
                        promotion_requirement += f"\n:x: 4 Month Service Stripes ({time_role})"

                    additional_requirement = "Participate actively in an SPD" + "\nInterviewed for a CoS position"
                    embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
                    embedVar.add_field(name="Additional Requirements", value=additional_requirement, inline=False)

                elif message.content == "O-1":
                    await confirmation.delete()
                    hosted_info = await get_hosted_info(member)
                    voyages_hosted = hosted_info[2]

                    if voyages_hosted >= 35:
                        promotion_requirement = f"\n:white_check_mark: Host 35 official voyages ({voyages_hosted}/35)"
                    else:
                        promotion_requirement = f"\n:x: Host 35 official voyages ({voyages_hosted}/35)"

                    conduct_roles = ["Honorable Conduct Medal", "Meritorious Conduct Medal", "Admirable Conduct Medal"]
                    conduct_role = next((role.name for role in member.roles if role.name in conduct_roles), None)

                    time_roles = ["4 Months Service Stripes", "6 Months Service Stripes", "8 Months Service Stripes",
                                  "12 Months Service Stripes", "18 Months Service Stripes", "24 Month Service Stripes"]
                    time_role = next((role.name for role in member.roles if role.name in time_roles), None)

                    if conduct_role:
                        promotion_requirement += f"\n:white_check_mark: Honorable Conduct Medal ({conduct_role})"
                    else:
                        promotion_requirement += f"\n:x: Honorable Conduct Medal ({conduct_role})"

                    if time_role:
                        promotion_requirement += f"\n:white_check_mark: 4 Month Service Stripes ({time_role})"
                    else:
                        promotion_requirement += f"\n:x: 4 Month Service Stripes ({time_role})"

                    embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
                    embedVar.add_field(name="Additional Requirements", value="Officer Board", inline=False)

                elif message.content == "cancel":
                    await ctx.send("Cancelled.")

        elif found_role == "Petty Officer | E-6":
            hosted_info = await get_hosted_info(member)
            voyages_hosted = hosted_info[2]

            if voyages_hosted >= 20:
                promotion_requirement = f"\n:white_check_mark: Host 20 official voyages ({voyages_hosted}/20)"
            else:
                promotion_requirement = f"\n:x: Host 20 official voyages ({voyages_hosted}/20)"

            additional_requirement = "Interviewed for a SL position" + "\nSNLA Complete" + "\nSNCO Board Passed" + "\nParticipate actively in a SPD"

            embedVar.add_field(name="Promotion Requirements", value=promotion_requirement, inline=False)
            embedVar.add_field(name="Additional Requirements", value=additional_requirement, inline=False)


        else:
            embedVar.add_field(name="Unknown", value="This user has too low of a rank for this command.", inline=False)
    else:
        embedVar.add_field(name="Unknown", value="This user has too low of a rank for this command.", inline=False)


async def get_subclass_points(member):
    carpenter = 0
    flex = 0
    cannoneer = 0
    helmsman = 0
    grenadier = 0
    surgeon = 0

    with open("Subclasses.txt", "r") as file:
        for line in file:
            parts = line.strip().split(" - ")
            if len(parts) >= 4 and parts[2] == str(member.id):
                subclass = parts[3]
                count = int(parts[4])
                if subclass.lower() == "carpenter":
                    carpenter += count
                elif subclass.lower() == "flex":
                    flex += count
                elif subclass.lower() == "cannoneer":
                    cannoneer += count
                elif subclass.lower() == "helm":
                    helmsman += count
                elif subclass.lower() == "grenadier":
                    grenadier += count
                elif subclass.lower() == "surgeon":
                    surgeon += count

        return carpenter, flex, cannoneer, helmsman, grenadier, surgeon


async def subclasses_field(embedVar, member):
    try:

        carpenter, flex, cannoneer, helmsman, grenadier, surgeon = await get_subclass_points(member)

        send = f"\n<:Planks:1256589596473692272> Carpenter: {carpenter}"
        send += f"\n<:Sword:1256589612202332313> Flex: {flex}"
        send += f"\n<:Cannon:1256589581894025236> Cannoneer: {cannoneer}"
        send += f"\n<:Wheel:1256589625993068665> Helm: {helmsman}"
        send += f"\n<:AthenaKeg:1030819975730040832> Grenadier: {grenadier}"
        send += f"\n:adhesive_bandage: Field Surgeon: {surgeon}"

        embedVar.add_field(name="Subclasses", value=send, inline=True)

    except Exception as e:
        embedVar.add_field(name="Subclasses", value="An Error Occurred", inline=True)
        print(e)


def get_highest_role_member(members):
    highest_role_member = None
    highest_role_position = -1

    for member in members:
        highest_role = max(member.roles, key=lambda role: role.position)

        if highest_role.position > highest_role_position:
            highest_role_position = highest_role.position
            highest_role_member = member

    return highest_role_member


def check_pingable(ctx, CO):
    if type(CO) == int:
        CO = discord.utils.get(ctx.guild.members, id=CO)

    choice = False
    with open("Settings.txt", 'r') as f:
        lines = f.readlines()

    for line in reversed(lines):
        line = line.strip()
        if line:
            parts = line.split(' - ')
            if parts[0] == str(CO.id):
                print(line)
                choice = parts[1] == 'True'
                break

    return choice


async def configure_award_message(ctx, target, channel, category, amount, award):
    role_index = identify_role_index(ctx, target)
    nextincommand = process_role_index(ctx, target, role_index)[0]

    pingable = check_pingable(ctx, nextincommand)
    if pingable == False:
        await channel.send(
            f"{target.display_name} has reached {amount} in the {category} category and is now eligible for {award}!")
    else:
        await channel.send(
            f"<@{nextincommand}>: {target.display_name} has reached {amount} in the {category} category and is now eligible for {award}!")


async def process_voyage_points(ctx, target, ishost):
    voyages_info = await get_voyage_info(target)
    voyages_value = voyages_info[2]
    hosted_info = await get_hosted_info(target)
    hosted_value = hosted_info[2]

    hosted_awards = {
        25: "Sea Service Ribbon",
        50: "Maritime Service Medal",
        100: "Legendary Service Medal",
        200: "Admirable Service Medal"
    }

    voyages_awards = {
        5: "Citation of Voyages",
        25: "Legion of Voyages",
        50: "Honorable Voyager Medal",
        100: "Meritorious Voyager Medal",
        200: "Admirable Voyager Medal"
    }

    if ishost == True:
        for value, award in hosted_awards.items():
            if hosted_value == value:
                if check_permissions(target, ["Junior Officer", "Senior Non Commissioned Officer",
                                              "Non Commissioned Officer", "Junior Enlisted"]):
                    channel = await get_ship_command_channel(ctx, target)
                else:
                    channel_name_fragment = "board-of-admiralty"
                    channel = discord.utils.find(lambda c: channel_name_fragment in c.name, ctx.guild.channels)

                if channel:
                    await configure_award_message(ctx, target, channel, "Hosted", value, award)

    for value, award in voyages_awards.items():
        if voyages_value == value:
            if check_permissions(target, ["Junior Officer", "Senior Non Commissioned Officer",
                                          "Non Commissioned Officer", "Junior Enlisted"]):
                channel = await get_ship_command_channel(ctx, target)
            else:
                channel_name_fragment = "board-of-admiralty"
                channel = discord.utils.find(lambda c: channel_name_fragment in c.name, ctx.guild.channels)

            if channel:
                await configure_award_message(ctx, target, channel, "Voyages", value, award)


async def process_subclass_points(ctx, user_name, subclass):
    print("processing subclass points")

    async def fetch_user_by_name(ctx, user_name):
        for member in ctx.guild.members:
            if member.display_name == user_name:
                return member
        return None

    def get_role(subclass, points):
        if subclass in ["carpenter", "flex", "helm", "cannoneer"]:
            if points >= 25:
                return f"Master {subclass.capitalize()}"
            elif points >= 15:
                return f"Pro {subclass.capitalize()}"
            elif points >= 5:
                return f"Adept {subclass.capitalize()}"
        elif subclass == "grenadier" and points >= 10:
            return "Grenadier"
        elif subclass == "surgeon" and points >= 5:
            return "Surgeon"
        return None

    target = await fetch_user_by_name(ctx, user_name)
    if not target:
        print(f"Error: User {user_name} not found.")
        return

    subclass_to_index = {
        'Carpenter': 0,
        'Flex': 1,
        'Cannoneer': 2,
        'Helm': 3,
        'Grenadier': 4,
        'Surgeon': 5
    }

    subclass_points = await get_subclass_points(target)
    subclass_points = subclass_points[subclass_to_index[subclass]]

    required_role = get_role(subclass.lower(), subclass_points)

    if required_role:
        user_roles = [role.name for role in target.roles]
        if required_role not in user_roles:
            if ((subclass.lower() in ["carpenter", "flex", "helm", "cannoneer"] and subclass_points in [5, 15, 25]) or
                    (subclass.lower() == "grenadier" and subclass_points == 10) or
                    (subclass.lower() == "surgeon" and subclass_points == 5)):

                if check_permissions(target, ["Junior Officer", "Senior Non Commissioned Officer",
                                              "Non Commissioned Officer", "Junior Enlisted"]):
                    channel = await get_ship_command_channel(ctx, target)
                else:
                    channel_name_fragment = "board-of-admiralty"
                    channel = discord.utils.find(lambda c: channel_name_fragment in c.name, ctx.guild.channels)

                if channel:
                    await configure_award_message(ctx, target, channel, subclass, subclass_points, required_role)
                else:
                    print("Channel not found :(")


async def get_ship_command_channel(ctx, target):
    ship_role = get_role_with_keyword(target, "USS")
    if ship_role:
        ship_name = ship_role.name.lower().strip()
        ship_name_last_word = ship_name.split()[-1]

        channel_name_keyword = f"{ship_name_last_word}-command"

        channel = discord.utils.find(lambda c: channel_name_keyword in c.name, ctx.guild.channels)
        if channel:
            return channel
        else:
            print(f"No channel found with the keyword {channel_name_keyword}")
    else:
        print("No ship role found.")
    return None


def search_display_names(guild, keyword):
    matching_members = []
    keyword_lower = keyword.lower()

    for member in guild.members:
        display_name_lower = member.display_name.lower()
        if keyword_lower in display_name_lower:
            matching_members.append(member)

    return matching_members


# Define the logbook_channel_id variable
logbook_channel_id = 935343526626078850

# Define the subclass points and log history storage
subclass_points = {}
log_history = {}

# Subclass synonyms
subclass_synonyms = {
    'Carpenter': ['carpenter', 'carp', 'bilge'],
    'Flex': ['flex', 'flexer', 'boarder'],
    'Cannoneer': ['cannoneer', 'cannon', 'gunner', 'canonneer', 'cannons'],
    'Helm': ['helm', 'helmsman', 'navigator'],
    'Surgeon': ['surgeon', 'doc', 'medic', 'field surgeon'],
    'Grenadier': ['grenadier', 'kegger', 'bomber']
}

# Reverse mapping of synonyms to main subclass names
synonym_to_subclass = {synonym: subclass for subclass, synonyms in subclass_synonyms.items() for synonym in synonyms}


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
            not check_permissions(ctx.author, ["Senior Officer", "Junior Officer"]) and
            not check_testing(ctx)):
        await ctx.respond(
            "You need to be the voyage host in order to do this command. If voyage host is unavailable, JO+ can do it.",
            ephemeral=True)
        return

    delete_duplicate_subclasses(log_id)

    content = message.content
    lines = content.split('\n')

    subclass_data = {}

    for line in lines:
        if '<@' in line and not 'log' in line:
            mention_index = line.find('<@')
            if mention_index != -1:
                user_mention_part = line[mention_index:]
                parts = [part.strip() for part in re.split(r'[ ,\-–]', user_mention_part) if part.strip()]

                # Handle the 's after the first mention
                if len(parts) > 1 and parts[1].lower() == "'s":
                    parts.pop(1)

                user_mention = parts[0]
                subclasses_raw = parts[1:]

                subclasses = []
                for subclass_raw in subclasses_raw:
                    subclass = synonym_to_subclass.get(subclass_raw.strip().lower(), None)
                    if subclass:
                        subclasses.append(subclass)
                    else:
                        break

                subclass_data[user_mention] = subclasses

    if not subclass_data:
        await ctx.respond("No valid subclass data found in the log message.", ephemeral=True)
        return

    response_message = "Subclass points have been successfully added for:\n"
    end_response = ""
    user_subclass_counts = {}

    for user_mention, subclasses in subclass_data.items():
        response_message += f"{user_mention}: {', '.join(subclasses)}\n"
        author_id = ctx.author.id
        log_link = f"https://discord.com/channels/{ctx.guild.id}/{logbook_channel_id}/{log_id}"
        try:
            target_id = int(user_mention.strip("<@!>'s:,*"))
        except ValueError:
            await ctx.respond(f"Invalid user mention: {user_mention}.", ephemeral=True)
            return

        if user_mention not in user_subclass_counts:
            user_subclass_counts[user_mention] = {}

        subclass_changes = []
        for subclass in subclasses:
            count = 1
            log_subclasses(author_id, log_link, target_id, subclass, count)

            member = discord.utils.get(ctx.guild.members, id=target_id)
            await process_subclass_points(ctx, member.display_name, subclass)

            subclass_to_index = {
                'Carpenter': 0,
                'Flex': 1,
                'Cannoneer': 2,
                'Helm': 3,
                'Grenadier': 4,
                'Surgeon': 5
            }

            all_points = await get_subclass_points(member)
            print(member.display_name)
            print(all_points)
            current_points = all_points[subclass_to_index[subclass]]
            print(current_points)
            previous_points = current_points - count
            print(previous_points)

            subclass_changes.append(f"{subclass} {previous_points}>{current_points}")

        if subclass_changes:
            end_response += f"{user_mention}: {', '.join(subclass_changes)}\n"

        if message.author.id == target_id:
            ishost = True
        else:
            ishost = False

        member = discord.utils.get(ctx.guild.members, id=target_id)
        await process_voyage_points(ctx, member, ishost)

    await ctx.respond(response_message + "\n" + end_response.rstrip('\n'), ephemeral=True)
    await message.add_reaction("<:kiri:1113326099200495736>")


@bot.slash_command(name="toggleawardping", description="Toggle award ping notifications on or off")
async def toggle_award_ping(ctx):
    with open('Settings.txt', 'r') as file:
        lines = file.readlines()

    lines.reverse()
    user_found = False

    for i, line in enumerate(lines):
        parts = line.strip().split(' - ')

        if parts[0] == str(ctx.author.id):
            parts[1] = "False" if parts[1] == "True" else "True"
            newchoice = parts[1]
            user_found = True
            lines[i] = ' - '.join(parts) + '\n'
            break

    if not user_found:
        print("not found")
        lines.append(f"{ctx.author.id} - True\n")
        newchoice = True

    lines.reverse()

    with open('Settings.txt', 'w') as file:
        file.writelines(lines)

    if newchoice == True:
        await ctx.respond("Settings updated: You will **now be pinged** in your command chat when awards are earned.",
                          ephemeral=True)
    else:
        await ctx.respond(
            "Settings updated: You will **no longer be pinged** in your command chat when awards are earned.",
            ephemeral=True)


'''

BREAK BREAK BREAK BREAK BREAK

'''


