#ADDNOTE

@bot.slash_command(name="addnote", description="Add a note to a Sailor Record (SNCO+)")
@option("sailor", description="Select the Sailor to add the note to")
@option("note", description="Write the note to add to the sailor")
async def addnote(ctx, sailor: discord.Member, note: str):
    required_roles = {"Senior Officer", "Junior Officer", "Senior Non Commissioned Officer"}
    executor_roles = {role.name for role in ctx.author.roles}

    if any(role in required_roles for role in executor_roles):
        Try:
			db_manager.add_note_to_file(sailor.id, ctx.author.id, note, datetime.utcnow())
			await ctx.respond(f"Note added for {sailor.mention}: {note}", ephemeral=True)
		except sqlite.Error as e:
			print(f"Error writing note: {e}")
			await ctx.respond(f"Error adding note for: {sailor.mention}, {e}", ephemeral=True)
        return
    await ctx.respond("You do not have the necessary permissions to use this command.", ephemeral=True)