class Commands:

    #ADDCOIN

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

    #ADD INFO

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

    #ADDNOTE

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


    #CHECK AWARDS

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

    #CHECK SQUADS

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

    #DELETE COIN

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

    #FORCE ADD

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

    #PING

    @bot.slash_command(name="ping", description="Check if the bot is online")
    async def ping(ctx):
        embedVar = discord.Embed(title="USN Hamtilities: Up and running!", color=discord.Color.blue())
        credits = "Owner and Creator: <@713484585874227220>\n Major coding help and bug fixer: <@690264788257079439>\nIdeas and BOA help: <@140988338432770058>\n"

        embedVar.add_field(name="Credits", value=credits, inline=True)
        await ctx.respond(f"Pong! We're up and running, sailor! Latency is {bot.latency}", embed=embedVar)

    #REMOVE NOTE 

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

    #ADD SUBCLASS

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

    #TOGGLE AWARD PING

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
