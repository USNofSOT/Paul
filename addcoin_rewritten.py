@bot.slash_command(name="addcoin", description="Add a challenge coin to a user")
# @discord.default_permissions(mute_members=True)
@option("target", description="Select the sailor to add your challenge coin to")
async def addcoin(ctx, target: discord.Member):

    try:
        # Determine coin type and handle database write based on rank
        # If adding New Coin Types just replciate the Case and ensure Rank Matches CASE SENSITIVE!
        match check_permissions(ctx.author, ["Senior Officer", "Junior Officer"]):
            case ["Senior Officer"]:
                coin_type = "Commanders Challenge Coin"
                display_name = ctx.author.display_name.split()[-1]
                database_manager.log_coin(target.id, coin_type, ctx.author.id, display_name, datetime.utcnow())  
                await ctx.respond(f"Added a {coin_type} to <@{target.id}>", ephemeral=True)
            case ["Junior Officer"]:
                coin_type = "Regular Challenge Coin"
                display_name = ctx.author.display_name.split()[-1]
                database_manager.log_coin(target.id, coin_type, ctx.author.id, display_name, datetime.utcnow())  
                await ctx.respond(f"Added a {coin_type} to <@{target.id}>", ephemeral=True)
            case _:  # All other cases
                await ctx.respond("You don't have a coin to give!", ephemeral=True)

    except sqlite3.Error as e:
        print(f"Error adding coin: {e}")
        await ctx.respond("An error occurred while adding the coin.", ephemeral=True)