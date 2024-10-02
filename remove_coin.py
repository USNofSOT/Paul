#removecoin
@bot.slash_command(name="removecoin", description="Remove a coin")
# @discord.default_permissions(administrator=True)
@option("target", description="Select the user to remove from")
async def deletecoin(ctx, target: discord.Member):
    if not check_permissions(ctx.author, ["Board of Admiralty"]):  # Removed specific user check
        await ctx.respond("This command is restricted to BOA members only.", ephemeral=True)
        return

    try:
        # Fetch coins for the target user from the database
        coins = database_manager.get_coins(target.id) 

        if not coins:
            await ctx.respond(f"No coins found for {target.mention}.", ephemeral=True)
            return

        # Display the coins to the user (using an embed for better presentation)
        embedVar = discord.Embed(title=f"Challenge Coins for {target.display_name}", color=0x00ff00)
        for i, coin in enumerate(coins):
            # Assuming coin[1] is coin_type, coin[3] is moderator_id
            moderator = ctx.guild.get_member(coin[3])
            moderator_name = moderator.display_name if moderator else "Unknown Moderator"
            embedVar.add_field(name=f"{i+1}. {coin[1]}", value=f"Given by: {moderator_name}", inline=False)
        editmessage = await ctx.respond(embed=embedVar)

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            msg = await bot.wait_for('message', check=check, timeout=60.0)   

            content = msg.content.strip()

            if content.isdigit():
                coin_index = int(content) - 1  # Adjust for 0-based indexing

                if 0 <= coin_index < len(coins):
                    # remove the selected coin from the database
                    database_manager.delete_coin(coins[coin_index][0])  # Assuming coin[0] is the coin ID

                    embedVar = discord.Embed(title="Challenge Coins", color=0x00ff00, 
                                            description=f"Deleted challenge coin from the database.")
                    await editmessage.edit(embed=embedVar)
                    return
                else:
                    await ctx.send("Invalid coin number. Please enter a valid number from the list.")
                    return
            else:
                await ctx.send("Invalid input. Please respond with a valid number to delete a coin.")

        except asyncio.TimeoutError:
            embedVar = discord.Embed(title="Challenge Coins", color=0x00ff00, description="Timed out.")
            await editmessage.edit(embed=embedVar)
            return

    except sqlite3.Error as e:
        print(f"Error deleting coin: {e}")
        await ctx.respond("An error occurred while deleting the coin.", ephemeral=True)