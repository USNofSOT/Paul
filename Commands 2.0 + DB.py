import sqlite3
import discord
from discord.ext import commands
from discord import option
import asyncio
from datetime import datetime

# Database Manager Class
class DatabaseManager:
    def __init__(self, db_name="your_database.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Coins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                member_id INTEGER,
                type TEXT,
                moderator INTEGER,
                old_name TEXT,
                timestamp TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS ModNotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_id INTEGER,
                moderator_id INTEGER,
                note TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Subclasses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author_id INTEGER,
                log_link TEXT,
                target_id INTEGER,
                subclass TEXT,
                count INTEGER,
                timestamp TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Settings (
                user_id INTEGER PRIMARY KEY,
                award_ping_enabled BOOLEAN
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Gamertags (
                user_id INTEGER PRIMARY KEY,
                gamertag TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Timezones (
                user_id INTEGER PRIMARY KEY,
                timezone TEXT
            )
        ''')

    # Coins Methods
    def log_coin(self, member_id, type, moderator, old_name, timestamp):
        try:
            self.cursor.execute('''
                INSERT INTO Coins (member_id, type, moderator, old_name, timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (member_id, type, moderator, old_name, timestamp))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error logging coin: {e}")

    def get_coins(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM Coins WHERE member_id = ?', (member_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving coins: {e}")
            return []

    def remove_coin(self, coin_id):
        try:
            self.cursor.execute('DELETE FROM Coins WHERE id = ?', (coin_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error deleting coin: {e}")

    # Moderation Note Methods
    def add_note_to_file(self, target_id, moderator_id, note):
        try:
            self.cursor.execute('''
                INSERT INTO ModNotes (target_id, moderator_id, note)
                VALUES (?, ?, ?)
            ''', (target_id, moderator_id, note))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding note: {e}")

    def get_notes(self, member_id):
        try:
            self.cursor.execute('SELECT * FROM ModNotes WHERE target_id = ?', (member_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error retrieving notes: {e}")
            return []

    def remove_note(self, note_id):
        try:
            self.cursor.execute('DELETE FROM ModNotes WHERE id = ?', (note_id,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error removing note: {e}")

    # Subclass Methods
    def log_subclasses(self, author_id, log_link, target_id, subclass, count, timestamp):
        try:
            self.cursor.execute('''
                INSERT INTO Subclasses (author_id, log_link, target_id, subclass, count, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (author_id, log_link, target_id, subclass, count, timestamp))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error logging subclasses: {e}")

    def get_subclass_points(self, member_id):
        try:
            self.cursor.execute('''
                SELECT subclass, SUM(count) 
                FROM Subclasses 
                WHERE target_id = ?
                GROUP BY subclass
            ''', (member_id,))
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"Error fetching subclass points: {e}")
            return []

    # Settings Methods
    def toggle_award_ping(self, user_id, new_choice):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO Settings (user_id, award_ping_enabled)
                VALUES (?, ?)
            ''', (user_id, new_choice))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error toggling award ping: {e}")

    def get_award_ping_setting(self, user_id):
        try:
            self.cursor.execute('SELECT award_ping_enabled FROM Settings WHERE user_id = ?', (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"Error retrieving award ping setting: {e}")
            return None

    # Gamertag and Timezone Methods
    def add_gamertag(self, user_id, gamertag):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO Gamertags (user_id, gamertag)
                VALUES (?, ?)
            ''', (user_id, gamertag))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding gamertag: {e}")

    def get_gamertag(self, user_id):
        try:
            self.cursor.execute('SELECT gamertag FROM Gamertags WHERE user_id = ?', (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"Error retrieving gamertag: {e}")
            return None

    def add_timezone(self, user_id, timezone):
        try:
            self.cursor.execute('''
                INSERT OR REPLACE INTO Timezones (user_id, timezone)
                VALUES (?, ?)
            ''', (user_id, timezone))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Error adding timezone: {e}")

    def get_timezone(self, user_id):
        try:
            self.cursor.execute('SELECT timezone FROM Timezones WHERE user_id = ?', (user_id,))
            row = self.cursor.fetchone()
            return row[0] if row else None
        except sqlite3.Error as e:
            print(f"Error retrieving timezone: {e}")
            return None

# Instantiate the Database Manager
db_manager = DatabaseManager()


# Bot Commands
#ADDCOIN
@bot.slash_command(name="addcoin", description="Add a challenge coin to a user")
@option("target", description="Select the user to add your challenge coin to")
@option("type", description="Choose coin type", autocomplete=get_coin)
async def addcoin(ctx, target: discord.Member, type: str):
    if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer"]):
        await ctx.respond("You don't have permissions to give challenge coins!", ephemeral=True)
        return

    display_name = ctx.author.display_name.split()[-1]
    if type == "Regular Challenge Coin":
        db_manager.log_coin(target.id, "Regular Challenge Coin", ctx.author.id, display_name, datetime.utcnow())
        await ctx.respond(f"Added a Regular Challenge Coin to <@{target.id}>", ephemeral=True)
    elif type == "Commanders Challenge Coin":
        if not check_permissions(ctx.author, ["Senior Officer"]):
            await ctx.respond("You don't have permissions to give a Commanders Challenge Coin!", ephemeral=True)
        else:
            db_manager.log_coin(target.id, "Commanders Challenge Coin", ctx.author.id, display_name, datetime.utcnow())
            await ctx.respond(f"Added a Commanders Challenge Coin to <@{target.id}>", ephemeral=True)
    else:
        await ctx.respond("Invalid type of coin.", ephemeral=True)

#ADDINFO

@bot.slash_command(name="addinfo", description="Add Gamertag or Timezone to yourself or another user")
@option("target", description="Select the user to add information to")
@option("gamertag", description="Enter the user's in-game username")
@option("timezone", description="Enter the user's timezone")
async def addinfo(ctx, target: discord.Member, gamertag: str = None, timezone: str = None):
    await ctx.defer(ephemeral=True)
    if not target:
        target = ctx.author

    if gamertag:
        db_manager.add_gamertag(target.id, gamertag)
    if timezone:
        db_manager.add_timezone(target.id, timezone)

    if gamertag and timezone:
        await ctx.respond(f"Information added for {target.name}: \nGamertag: {gamertag}\nTimezone: {timezone}")
    elif gamertag:
        await ctx.respond(f"Information added for {target.name}: \nGamertag: {gamertag}")
    elif timezone:
        await ctx.respond(f"Information added for {target.name}: \nTimezone: {timezone}")
    else:
        await ctx.respond("You didn't add anything...")

#ADDNOTE

@bot.slash_command(name="addnote", description="Add a moderation note to a user (SNCO+)")
@option("target", description="Select the user to add the note to")
@option("note", description="Write the note to add to the user")
async def addnote(ctx, target: discord.Member, note: str):
    required_roles = {"Senior Officer", "Junior Officer", "Senior Non Commissioned Officer"}
    executor_roles = {role.name for role in ctx.author.roles}

    if not any(role in required_roles for role in executor_roles):
        await ctx.respond("You do not have the necessary permissions to use this command.", ephemeral=True)
        return

    db_manager.add_note_to_file(target.id, ctx.author.id, note)
    await ctx.respond(f"Note added for {target.mention}: {note}", ephemeral=True)

#DELETECOIN

@bot.slash_command(name="deletecoin", description="Delete a challenge coin from a user")
@option("target", description="Select the user to delete from")
async def deletecoin(ctx, target: discord.Member):
    if not check_permissions(ctx.author, ["Board of Admiralty"]):
        await ctx.respond("This command is restricted to BOA members only.", ephemeral=True)
        return

    coins = db_manager.get_coins(target.id)
    if not coins:
        await ctx.respond(f"No coins found for {target.mention}", ephemeral=True)
        return

    coin_list = "\n".join([f"{index + 1}. {coin['type']} - {coin['moderator']} (ID: {coin['id']})" for index, coin in enumerate(coins)])

    await ctx.respond(f"Here are the coins for {target.mention}:\n{coin_list}\nPlease respond with the coin ID to delete.", ephemeral=True)

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        msg = await bot.wait_for('message', check=check, timeout=60.0)
        content = msg.content.strip()
        if content.isdigit():
            coin_id = int(content)
            db_manager.remove_coin(coin_id)
            await ctx.respond(f"Deleted coin with ID {coin_id}.", ephemeral=True)
        else:
            await ctx.send("Invalid input. Please provide a valid coin ID.", ephemeral=True)
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No coin deleted.", ephemeral=True)

#CHECKAWARDS
@bot.slash_command(name="check_awards", description="Check awards to ensure everyone is up-to-date")
@option("target_role", description="Select the role to check! Ships and squads work best.")
async def check_awards(ctx, target_role: discord.Role = None):
    logging.info(f"check_awards command invoked by {ctx.author.display_name}")
    await ctx.defer(ephemeral=True)

    async def process_member(member):
        try:
            # Fetch subclass points and voyages for the member from the database
            subclass_points = db_manager.get_subclass_points(member.id)
            points = {subclass: count for subclass, count in subclass_points}
            
            # Default points for subclasses if no data is found
            points = {
                "carpenter": points.get("carpenter", 0),
                "flex": points.get("flex", 0),
                "cannoneer": points.get("cannoneer", 0),
                "helm": points.get("helm", 0),
                "grenadier": points.get("grenadier", 0),
                "surgeon": points.get("surgeon", 0)
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

            # Determine missing roles
            required_roles = {subclass: get_role(subclass, points[subclass]) for subclass in points}
            user_roles = [role.name for role in member.roles]
            missing_roles = ""

            for subclass, role in required_roles.items():
                if role and role not in user_roles:
                    missing_roles += f"<@{member.id}> is missing the {role}\n"

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

#CHECKSQUADS
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

#FORCEADD
@bot.slash_command(name="forceadd", description="Force-add voyages, subclasses, or other data to a user. (BOA ONLY!)")
@option("target", description="Select the user to forceadd data to")
@option("voyages", description="Add total voyages. Note: A user may need hosted voyages added separately.")
@option("hosted", description="Add hosted voyages. Note: A user may need voyage count added separately.")
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

    # Log voyages in the database
    if voyages is not None:
        if is_full_number(voyages):
            db_manager.log_forceadd(target.id, "Regular", voyages, ctx.author.id, datetime.utcnow())
            added += f"Voyages: {voyages}\n"
        else:
            added += "Voyages were not added because the number was not a whole number."

    if hosted is not None:
        if is_full_number(hosted):
            db_manager.log_forceadd(target.id, "Hosted", hosted, ctx.author.id, datetime.utcnow())
            added += f"Hosted: {hosted}\n"
        else:
            added += "Hosted were not added because the number was not a whole number."

    # Log subclass points in the database
    subclasses = {
        "Carpenter": carpenter,
        "Cannoneer": cannoneer,
        "Flex": flex,
        "Helm": helm,
        "Surgeon": surgeon,
        "Grenadier": grenadier
    }
    for subclass_name, subclass_points in subclasses.items():
        if subclass_points is not None:
            if is_full_number(subclass_points):
                db_manager.log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, subclass_name, subclass_points, datetime.utcnow())
                added += f"{subclass_name}: {subclass_points}\n"
            else:
                added += f"{subclass_name} was not added because the number was not a whole number.\n"

    # Log coins if applicable
    if coin and coinowner is not None:
        if coin == "Regular Challenge Coin":
            db_manager.log_coin(target.id, "Regular Challenge Coin", "0", coinowner, datetime.utcnow())
            added += f"Regular Coin: {coinowner}\n"
        elif coin == "Commanders Challenge Coin":
            db_manager.log_coin(target.id, "Commanders Challenge Coin", "0", coinowner, datetime.utcnow())
            added += f"Commanders Coin: {coinowner}\n"
        else:
            added += "Please ensure you've added both a coin and coinowner. If it errors, try clicking the options for coin instead of typing."

    await ctx.respond(f"Complete: \n{added}", ephemeral=True)

#ADDSUBCLASS
@bot.slash_command(name="addsubclass", description="Add subclass points for your log")
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

    if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer", "Senior Non Commissioned Officer", "Non Commissioned Officer"]) and not check_testing(ctx):
        await ctx.respond("Only current voyage hosts can add to their logs!", ephemeral=True)
        return

    if (message.author != ctx.author and
        not check_permissions(ctx.author, ["Senior Officer", "Junior Officer"]) and not check_testing(ctx)):
        await ctx.respond("You need to be the voyage host in order to do this command. If voyage host is unavailable, JO+ can do it.", ephemeral=True)
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

            subclasses = [synonym_to_subclass.get(subclass_raw.strip().lower(), None) for subclass_raw in subclasses_raw if synonym_to_subclass.get(subclass_raw.strip().lower())]

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

#MEMBER
@bot.slash_command(name="member", description="Check information of a user or all users in a role")
@option("target", description="Choose a user or role to grab info for")
@option("level", description="Choose info view", autocomplete=get_levels)
async def member(ctx, target: discord.Member | discord.Role = None, level: str = None):
    logging.info(f"member command invoked by {ctx.author.display_name}")
    if target is None:
        target = ctx.author

    if level is None:
        level = "Default"

    # Handle when the target is a role
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
                # Time in server (Assuming this info is not stored in DB)
                time_in_server_field(embedVar, member)

                # Get additional info (gamertag, timezone, etc.) from the database
                await otherinfo_field(embedVar, member)

                # Get voyage info from the database
                voyages_info = db_manager.get_voyage_info(member.id)
                if voyages_info:
                    embedVar.add_field(name="Voyage Info", value=f"Total Voyages: {voyages_info['total']}, Hosted Voyages: {voyages_info['hosted']}")
                
                # Get hosted info from the database
                hosted_info = db_manager.get_hosted_info(member.id)
                if hosted_info:
                    embedVar.add_field(name="Hosted Info", value=f"Hosted: {hosted_info['total']}")
                
                # Get subclass points from the database
                subclasses_info = db_manager.get_subclass_points(member.id)
                if subclasses_info:
                    subclasses = ", ".join([f"{subclass}: {count}" for subclass, count in subclasses_info.items()])
                    embedVar.add_field(name="Subclass Points", value=subclasses)
                
                # Get coins from the database
                coins_info = db_manager.get_coins(member.id)
                if coins_info:
                    coins = ", ".join([f"{coin['type']} from {coin['moderator']}" for coin in coins_info])
                    embedVar.add_field(name="Coins", value=coins)

                embed_messages.append(embedVar)

            elif level.lower() == "moderation":
                # Check permissions for moderation info
                if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer", "Senior Non Commissioned Officer", "Non Commissioned Officer"]):
                    embedVar.add_field(name="Error", value="You don't have permission to view moderation details.")
                    embed_messages.append(embedVar)
                    return

                # Add basic member info
                time_in_server_field(embedVar, member)
                embedVar.add_field(name="User ID", value=str(member.id), inline=True)

                # Get subclass points from the database
                subclasses_info = db_manager.get_subclass_points(member.id)
                if subclasses_info:
                    subclasses = ", ".join([f"{subclass}: {count}" for subclass, count in subclasses_info.items()])
                    embedVar.add_field(name="Subclass Points", value=subclasses)

                # Add role, name, moderation details, and notes (Assuming these come from DB or other sources)
                await role_field(embedVar, member)
                await name_field(embedVar, member)
                await moderation_field(embedVar, member)
                await notes_field(embedVar, member)

                embed_messages.append(embedVar)

            elif level.lower() == "promotion":
                # Assuming this is not directly linked to the DB
                await promotions_field(ctx, embedVar, member)
                embedVar.set_footer(text="Promotion data may be inaccurate.")
                embed_messages.append(embedVar)

            else:
                embedVar.add_field(name="Error", value="The value you inputted into the `level` field is not a valid choice.")
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


#TOGGLEAWARDPING
@bot.slash_command(name="toggleawardping", description="Toggle award ping notifications on or off")
async def toggle_award_ping(ctx):
    user_id = ctx.author.id
    current_setting = db_manager.get_award_ping_setting(user_id)

    new_choice = not current_setting if current_setting is not None else True
    db_manager.toggle_award_ping(user_id, new_choice)

    if new_choice:
        await ctx.respond("Settings updated: You will **now be pinged** in your command chat when awards are earned.", ephemeral=True)
    else:
        await ctx.respond("Settings updated: You will **no longer be pinged** in your command chat when awards are earned.", ephemeral=True)

#REMOVENOTE
@bot.slash_command(name="removenote", description="Remove a moderation note from a user (SO+)")
@option("noteid", description="Write the number of the note to be removed")
async def removenote(ctx, noteid: int):
    if not check_permissions(ctx.author, ["Senior Officer"]):
        await ctx.defer(ephemeral=True)
        await ctx.followup.send("This command is only available for Senior Officers or higher.")
        return

    try:
        db_manager.remove_note(noteid)
        await ctx.respond(f"Note with ID {noteid} has been removed.", ephemeral=True)
    except sqlite3.Error as e:
        await ctx.respond(f"Error removing note: {e}", ephemeral=True)


----BREAK BREAK BREAK BREAK BREAK BREAK----

#suggestion for combining the moderator functions into a single function SailorFile (tbd)

@bot.slash_command(name="SailorFile", description="Manage Sailor Files: 1) Add Coin, 2) Add Info, 3) Add Note, 4) Delete Coin, 5) Force Add, 6) Remove Note, 7) Toggle Award Ping")
@option("option", description="Select a command (1-7)", choices=["1", "2", "3", "4", "5", "6", "7"])
async def sailorfile(ctx, option: str):
    """
    Combined /SailorFile command that presents options for the user to choose.
    """
    try:
        # Menu for choosing which action to take based on the number provided by the user
        if option == "1":
            await add_coin(ctx)
        elif option == "2":
            await add_info(ctx)
        elif option == "3":
            await add_note(ctx)
        elif option == "4":
            await delete_coin(ctx)
        elif option == "5":
            await force_add(ctx)
        elif option == "6":
            await remove_note_command(ctx)
        elif option == "7":
            await toggle_award_ping(ctx)
        else:
            await ctx.respond("Invalid option. Please choose a number between 1-7.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"An error occurred while executing the command: {e}", ephemeral=True)

# ADD COIN (Option 1)
async def add_coin(ctx):
    # Check permission first
    if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer"]):
        await ctx.respond("You don't have permissions to give challenge coins!", ephemeral=True)
        return
    
    # Get target and type options
    target = await prompt_target(ctx)
    if target is None:
        return
    coin_type = await prompt_coin_type(ctx)
    if coin_type is None:
        return

    display_name = ctx.author.display_name.split()[-1]
    if coin_type == "Regular Challenge Coin":
        db_manager.log_coin(target.id, "Regular Challenge Coin", ctx.author.id, display_name, datetime.utcnow())
        await ctx.respond(f"Added a Regular Challenge Coin to <@{target.id}>", ephemeral=True)
    elif coin_type == "Commanders Challenge Coin":
        if not check_permissions(ctx.author, ["Senior Officer"]):
            await ctx.respond("You don't have permissions to give a Commanders Challenge Coin!", ephemeral=True)
        else:
            db_manager.log_coin(target.id, "Commanders Challenge Coin", ctx.author.id, display_name, datetime.utcnow())
            await ctx.respond(f"Added a Commanders Challenge Coin to <@{target.id}>", ephemeral=True)
    else:
        await ctx.respond("Invalid type of coin.", ephemeral=True)

# ADD INFO (Option 2)
async def add_info(ctx):
    target = await prompt_target(ctx)
    if target is None:
        return
    
    # Ensure permission
    allowed_roles = ["Senior Officer", "Junior Officer", "Senior Non Commissioned Officer", "NRC Department"]
    author_roles = [role.name for role in ctx.author.roles]
    if not any(role in allowed_roles for role in author_roles) and ctx.author != target:
        await ctx.respond("You don't have permission to edit this user's information.", ephemeral=True)
        return
    
    gamertag = await prompt_gamertag(ctx)
    timezone = await prompt_timezone(ctx)
    
    if gamertag:
        db_manager.add_gamertag(target.id, gamertag)
    if timezone:
        db_manager.add_timezone(target.id, timezone)

    if gamertag and timezone:
        await ctx.respond(f"Information added for {target.name}: \nGamertag: {gamertag}\nTimezone: {timezone}")
    elif gamertag:
        await ctx.respond(f"Information added for {target.name}: \nGamertag: {gamertag}")
    elif timezone:
        await ctx.respond(f"Information added for {target.name}: \nTimezone: {timezone}")
    else:
        await ctx.respond("You didn't add anything...", ephemeral=True)

# ADD NOTE (Option 3)
async def add_note(ctx):
    target = await prompt_target(ctx)
    if target is None:
        return
    
    note = await prompt_note_content(ctx)
    if note is None:
        return

    required_roles = {"Senior Officer", "Junior Officer", "Senior Non Commissioned Officer"}
    executor_roles = {role.name for role in ctx.author.roles}
    
    if not any(role in required_roles for role in executor_roles):
        await ctx.respond("You do not have the necessary permissions to add a note.", ephemeral=True)
        return
    
    db_manager.add_note_to_file(target.id, ctx.author.id, note)
    await ctx.respond(f"Note added for {target.mention}: {note}", ephemeral=True)

# DELETE COIN (Option 4)
async def delete_coin(ctx):
    if not check_permissions(ctx.author, ["Board of Admiralty"]):
        await ctx.respond("This command is restricted to BOA members only.", ephemeral=True)
        return
    
    target = await prompt_target(ctx)
    if target is None:
        return
    
    coins = db_manager.get_coins(target.id)
    if not coins:
        await ctx.respond(f"No coins found for {target.mention}", ephemeral=True)
        return
    
    coin_id = await prompt_coin_id(ctx, coins)
    if coin_id is None:
        return

    db_manager.remove_coin(coin_id)
    await ctx.respond(f"Deleted coin with ID {coin_id}.", ephemeral=True)

# FORCE ADD (Option 5)
async def force_add(ctx):
    if not check_permissions(ctx.author, ["Board of Admiralty"]):
        await ctx.respond("This command is restricted to BOA members only.", ephemeral=True)
        return
    
    target = await prompt_target(ctx)
    if target is None:
        return
    
    voyages, hosted, carpenter, cannoneer, flex, helm, surgeon, grenadier, coin, coinowner = await prompt_forceadd_options(ctx)
    
    added = ""
    if voyages:
        db_manager.log_forceadd(target.id, "Regular", voyages, ctx.author.id, datetime.utcnow())
        added += f"Voyages: {voyages}\n"
    if hosted:
        db_manager.log_forceadd(target.id, "Hosted", hosted, ctx.author.id, datetime.utcnow())
        added += f"Hosted: {hosted}\n"
    
    # Log subclass points and coins
    subclasses = {"Carpenter": carpenter, "Cannoneer": cannoneer, "Flex": flex, "Helm": helm, "Surgeon": surgeon, "Grenadier": grenadier}
    for subclass_name, points in subclasses.items():
        if points:
            db_manager.log_subclasses(ctx.author.id, "BOA OVERRIDE", target.id, subclass_name, points, datetime.utcnow())
            added += f"{subclass_name}: {points}\n"
    
    if coin and coinowner:
        db_manager.log_coin(target.id, coin, "0", coinowner, datetime.utcnow())
        added += f"{coin}: {coinowner}\n"
    
    await ctx.respond(f"Complete: \n{added}", ephemeral=True)

# REMOVE NOTE (Option 6)
async def remove_note_command(ctx):
    if not check_permissions(ctx.author, ["Senior Officer"]):
        await ctx.respond("This command is only available to Senior Officers or higher.", ephemeral=True)
        return
    
    note_id = await prompt_note_id(ctx)
    if note_id is None:
        return
    
    db_manager.remove_note(note_id)
    await ctx.respond(f"Note with ID {note_id} has been removed.", ephemeral=True)

# TOGGLE AWARD PING (Option 7)
async def toggle_award_ping(ctx):
    user_id = ctx.author.id
    current_setting = db_manager.get_award_ping_setting(user_id)

    new_choice = not current_setting if current_setting is not None else True
    db_manager.toggle_award_ping(user_id, new_choice)

    if new_choice:
        await ctx.respond("Settings updated: You will **now be pinged** in your command chat when awards are earned.", ephemeral=True)
    else:
        await ctx.respond("Settings updated: You will **no longer be pinged** in your command chat when awards are earned.", ephemeral=True)


# Helper functions to prompt the user for input in a step-by-step manner
async def prompt_target(ctx):
    """Prompts the user to select a target user."""
    await ctx.respond("Please mention the target user.", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        target = msg.mentions[0] if msg.mentions else None
        if target:
            return target
        else:
            await ctx.respond("No valid user mentioned.", ephemeral=True)
            return None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No user selected.", ephemeral=True)
        return None

async def prompt_coin_type(ctx):
    """Prompts the user to select a coin type."""
    await ctx.respond("Please select the coin type: 1) Regular Challenge Coin, 2) Commanders Challenge Coin", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        return "Regular Challenge Coin" if msg.content == "1" else "Commanders Challenge Coin" if msg.content == "2" else None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No coin type selected.", ephemeral=True)
        return None

async def prompt_gamertag(ctx):
    """Prompts the user to enter a gamertag."""
    await ctx.respond("Please enter the gamertag (or type 'skip').", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        return msg.content if msg.content.lower() != "skip" else None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No gamertag provided.", ephemeral=True)
        return None

async def prompt_timezone(ctx):
    """Prompts the user to enter a timezone."""
    await ctx.respond("Please enter the timezone (or type 'skip').", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        return msg.content if msg.content.lower() != "skip" else None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No timezone provided.", ephemeral=True)
        return None

async def prompt_note_content(ctx):
    """Prompts the user to enter a note."""
    await ctx.respond("Please enter the note content.", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        return msg.content if msg.content else None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No note provided.", ephemeral=True)
        return None

async def prompt_coin_id(ctx, coins):
    """Prompts the user to select a coin ID."""
    coin_list = "\n".join([f"{index + 1}. {coin['type']} - {coin['moderator']} (ID: {coin['id']})" for index, coin in enumerate(coins)])
    await ctx.respond(f"Here are the coins:\n{coin_list}\nPlease respond with the coin ID to delete.", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        return int(msg.content) if msg.content.isdigit() else None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No coin selected.", ephemeral=True)
        return None

async def prompt_forceadd_options(ctx):
    """Prompts the user to provide force-add options."""
    # Collect all necessary inputs, similar to the other prompt functions
    await ctx.respond("Please enter voyage, hosted, carpenter, cannoneer, flex, helm, surgeon, grenadier points, or 'skip' if not applicable.", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=120.0)
        # Parse user input and return as necessary data for force-add options
        voyages, hosted, carpenter, cannoneer, flex, helm, surgeon, grenadier, coin, coinowner = None, None, None, None, None, None, None, None, None, None
        return voyages, hosted, carpenter, cannoneer, flex, helm, surgeon, grenadier, coin, coinowner
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No options provided.", ephemeral=True)
        return None, None, None, None, None, None, None, None, None, None

async def prompt_note_id(ctx):
    """Prompts the user to select a note ID for deletion."""
    await ctx.respond("Please enter the note ID to remove.", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        return int(msg.content) if msg.content.isdigit() else None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No note ID provided.", ephemeral=True)
        return None

-------BREAK BREAK BREAK BREAK BREAK ---------

@bot.slash_command(name="Report", description="Generate reports: 1) Squad Report, 2) Awards Report, 3) Member Report, 4) Moderation Report, 5) Promotion Report")
@option("option", description="Select a report type (1-5)", choices=["1", "2", "3", "4", "5"])
async def report(ctx, option: str):
    """
    Combined /Report command that presents options for the user to choose.
    """
    try:
        # Menu for choosing which report to generate based on the number provided by the user
        if option == "1":
            await squad_report(ctx)  # Option 1: Squad Report
        elif option == "2":
            await awards_report(ctx)  # Option 2: Awards Report
        elif option == "3":
            await member_report(ctx)  # Option 3: Member Report (Default)
        elif option == "4":
            await moderation_report(ctx)  # Option 4: Moderation Report
        elif option == "5":
            await promotion_report(ctx)  # Option 5: Promotion Report
        else:
            await ctx.respond("Invalid option. Please choose a number between 1-5.", ephemeral=True)
    except Exception as e:
        await ctx.respond(f"An error occurred while executing the command: {e}", ephemeral=True)

# SQUAD REPORT (Option 1)
async def squad_report(ctx):
    """
    Check Squads Report: Ensure all Junior Enlisted members are in a squad.
    """
    squad_keyword = "Squad"
    junior_enlisted_role_name = "Junior Enlisted"
    junior_enlisted_role = discord.utils.get(ctx.guild.roles, name=junior_enlisted_role_name)

    if not junior_enlisted_role:
        await ctx.respond(f"Role '{junior_enlisted_role_name}' not found.", ephemeral=True)
        return

    target_role = await prompt_target_role(ctx)
    if target_role is None:
        return

    if target_role:
        members_to_check = [member for member in target_role.members if junior_enlisted_role in member.roles]
    else:
        members_to_check = [member for member in ctx.guild.members if junior_enlisted_role in member.roles]

    no_squad_members = []
    for member in members_to_check:
        has_squad_role = any(squad_keyword.lower() in role.name.lower() for role in member.roles)
        if not has_squad_role:
            no_squad_members.append(member.mention)

    if no_squad_members:
        if target_role:
            await ctx.respond(f"JE without a 'Squad' role in {target_role}:\n" + "\n".join(no_squad_members))
        else:
            await ctx.respond(f"JE without a 'Squad' role in the server:\n" + "\n".join(no_squad_members))
    else:
        await ctx.respond("All members have a 'Squad' role.", ephemeral=True)

# AWARDS REPORT (Option 2)
async def awards_report(ctx):
    """
    Awards Report: Check awards to ensure members are up-to-date.
    """
    logging.info(f"Awards report invoked by {ctx.author.display_name}")
    await ctx.defer(ephemeral=True)

    target_role = await prompt_target_role(ctx)
    if target_role is None:
        return

    async def process_member(member):
        try:
            subclass_points = db_manager.get_subclass_points(member.id)
            hosted_info = db_manager.get_hosted_info(member.id)
            voyages_info = db_manager.get_voyage_info(member.id)

            # Logic for checking awards and missing roles
            missing_roles = ""
            required_roles = {
                "carpenter": "Master Carpenter", "flex": "Master Flex", "cannoneer": "Master Cannoneer", "helm": "Master Helm",
                "grenadier": "Grenadier", "surgeon": "Field Surgeon"
            }

            user_roles = [role.name for role in member.roles]
            target_id = member.id

            for subclass, role_name in required_roles.items():
                if role_name not in user_roles and subclass_points.get(subclass, 0) > 0:
                    missing_roles += f"<@{target_id}> is missing the {role_name}\n"

            hosted_value = hosted_info.get('total', 0)
            voyages_value = voyages_info.get('total', 0)

            hosted_awards = {
                200: "Admirable Service Medal", 100: "Legendary Service Medal", 50: "Maritime Service Medal", 25: "Sea Service Ribbon"
            }
            voyages_awards = {
                200: "Admirable Voyager Medal", 100: "Meritorious Voyager Medal", 50: "Honorable Voyager Medal", 25: "Legion of Voyages"
            }

            for value, award in hosted_awards.items():
                if hosted_value >= value and award not in user_roles:
                    missing_roles += f"<@{target_id}> is missing the {award}\n"
            for value, award in voyages_awards.items():
                if voyages_value >= value and award not in user_roles:
                    missing_roles += f"<@{target_id}> is missing the {award}\n"

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

# MEMBER REPORT (Option 3) - Default
async def member_report(ctx):
    """
    Member Report: Retrieve basic member information (Default view).
    """
    logging.info(f"Member report invoked by {ctx.author.display_name}")
    
    target_role_or_member = await prompt_target(ctx)
    if target_role_or_member is None:
        return
    
    if isinstance(target_role_or_member, discord.Role):
        members = target_role_or_member.members
    else:
        members = [target_role_or_member]

    if len(members) >= 28:
        await ctx.respond("Too big of a role! Ship or smaller, please.")
        return

    await ctx.defer(ephemeral=True)

    embed_messages = []
    async def process_member(member):
        try:
            embedVar = discord.Embed(title=member.display_name, description=f"<@{member.id}>", color=discord.Color.blue())

            time_in_server_field(embedVar, member)

            voyages_info = db_manager.get_voyage_info(member.id)
            hosted_info = db_manager.get_hosted_info(member.id)
            subclasses_info = db_manager.get_subclass_points(member.id)
            coins_info = db_manager.get_coins(member.id)

            if voyages_info:
                embedVar.add_field(name="Voyages", value=f"Total: {voyages_info['total']}, Hosted: {voyages_info['hosted']}")
            if subclasses_info:
                subclasses = ", ".join([f"{subclass}: {count}" for subclass, count in subclasses_info.items()])
                embedVar.add_field(name="Subclass Points", value=subclasses)
            if coins_info:
                coins = ", ".join([f"{coin['type']} from {coin['moderator']}" for coin in coins_info])
                embedVar.add_field(name="Coins", value=coins)

            embed_messages.append(embedVar)
        except Exception as e:
            logging.error(f"Error processing member {member.display_name}: {e}")
            embedVar.add_field(name="Error", value=f"An error occurred while processing {member.display_name}: {e}")
            embed_messages.append(embedVar)

    await asyncio.gather(*[process_member(member) for member in members])

    for embed in embed_messages:
        try:
            await ctx.respond(embed=embed)
        except Exception as e:
            logging.error(f"Error responding with embed for {ctx.author.display_name}: {e}")
            await ctx.respond(f"An error occurred while sending the response.", ephemeral=True)

# MODERATION REPORT (Option 4)
async def moderation_report(ctx):
    """
    Moderation Report: Detailed information for moderation purposes (requires permission).
    """
    logging.info(f"Moderation report invoked by {ctx.author.display_name}")
    
    target_role_or_member = await prompt_target(ctx)
    if target_role_or_member is None:
        return

    # Permission check for moderation-level reports
    if not check_permissions(ctx.author, ["Senior Officer", "Junior Officer", "Senior Non Commissioned Officer", "Non Commissioned Officer"]):
        await ctx.respond("You don't have permission to view moderation details.", ephemeral=True)
        return

    if isinstance(target_role_or_member, discord.Role):
        members = target_role_or_member.members
    else:
        members = [target_role_or_member]

    if len(members) >= 28:
        await ctx.respond("Too big of a role! Ship or smaller, please.")
        return

    await ctx.defer(ephemeral=True)

    embed_messages = []

    async def process_member(member):
        try:
            embedVar = discord.Embed(title=member.display_name, description=f"<@{member.id}>", color=discord.Color.blue())
            
            # Time in server
            time_in_server_field(embedVar, member)

            # Retrieve moderation details (subclass points, notes, etc.)
            voyages_info = db_manager.get_voyage_info(member.id)
            hosted_info = db_manager.get_hosted_info(member.id)
            subclasses_info = db_manager.get_subclass_points(member.id)
            coins_info = db_manager.get_coins(member.id)
            notes_info = db_manager.get_notes(member.id)

            if voyages_info:
                embedVar.add_field(name="Voyages", value=f"Total: {voyages_info['total']}, Hosted: {voyages_info['hosted']}")
            if subclasses_info:
                subclasses = ", ".join([f"{subclass}: {count}" for subclass, count in subclasses_info.items()])
                embedVar.add_field(name="Subclass Points", value=subclasses)
            if coins_info:
                coins = ", ".join([f"{coin['type']} from {coin['moderator']}" for coin in coins_info])
                embedVar.add_field(name="Coins", value=coins)
            if notes_info:
                notes = "\n".join([f"Note: {note['note']} by {note['moderator']}" for note in notes_info])
                embedVar.add_field(name="Moderation Notes", value=notes)

            embed_messages.append(embedVar)
        except Exception as e:
            logging.error(f"Error processing member {member.display_name}: {e}")
            embedVar.add_field(name="Error", value=f"An error occurred while processing {member.display_name}: {e}")
            embed_messages.append(embedVar)

    await asyncio.gather(*[process_member(member) for member in members])

    for embed in embed_messages:
        try:
            await ctx.respond(embed=embed)
        except Exception as e:
            logging.error(f"Error responding with embed for {ctx.author.display_name}: {e}")
            await ctx.respond(f"An error occurred while sending the response.", ephemeral=True)

# PROMOTION REPORT (Option 5)
async def promotion_report(ctx):
    """
    Promotion Report: Retrieve promotion-related information for members.
    """
    logging.info(f"Promotion report invoked by {ctx.author.display_name}")
    
    target_role_or_member = await prompt_target(ctx)
    if target_role_or_member is None:
        return

    if isinstance(target_role_or_member, discord.Role):
        members = target_role_or_member.members
    else:
        members = [target_role_or_member]

    if len(members) >= 28:
        await ctx.respond("Too big of a role! Ship or smaller, please.")
        return

    await ctx.defer(ephemeral=True)

    embed_messages = []

    async def process_member(member):
        try:
            embedVar = discord.Embed(title=member.display_name, description=f"<@{member.id}>", color=discord.Color.blue())
            
            # Fetch promotion-related info from the database or logic (if applicable)
            promotion_info = await fetch_promotion_info(member)
            if promotion_info:
                embedVar.add_field(name="Promotion Status", value=promotion_info)

            embed_messages.append(embedVar)
        except Exception as e:
            logging.error(f"Error processing member {member.display_name}: {e}")
            embedVar.add_field(name="Error", value=f"An error occurred while processing {member.display_name}: {e}")
            embed_messages.append(embedVar)

    await asyncio.gather(*[process_member(member) for member in members])

    for embed in embed_messages:
        try:
            await ctx.respond(embed=embed)
        except Exception as e:
            logging.error(f"Error responding with embed for {ctx.author.display_name}: {e}")
            await ctx.respond(f"An error occurred while sending the response.", ephemeral=True)

# Helper functions to prompt the user for input
async def prompt_target(ctx):
    """Prompts the user to select a target user or role."""
    await ctx.respond("Please mention the target user or role.", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        target = msg.mentions[0] if msg.mentions else discord.utils.get(ctx.guild.roles, name=msg.content)
        if target:
            return target
        else:
            await ctx.respond("No valid user or role mentioned.", ephemeral=True)
            return None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No target selected.", ephemeral=True)
        return None

async def prompt_target_role(ctx):
    """Prompts the user to select a target role."""
    await ctx.respond("Please mention the target role.", ephemeral=True)
    try:
        msg = await bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == ctx.channel, timeout=60.0)
        target_role = discord.utils.get(ctx.guild.roles, name=msg.content)
        if target_role:
            return target_role
        else:
            await ctx.respond("No valid role mentioned.", ephemeral=True)
            return None
    except asyncio.TimeoutError:
        await ctx.respond("Timeout. No role selected.", ephemeral=True)
        return None

