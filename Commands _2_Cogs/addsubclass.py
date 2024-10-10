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