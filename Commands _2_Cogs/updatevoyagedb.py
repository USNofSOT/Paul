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