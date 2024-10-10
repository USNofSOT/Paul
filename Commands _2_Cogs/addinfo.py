


#addinfo
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