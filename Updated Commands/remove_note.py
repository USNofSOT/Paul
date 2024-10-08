#REMOVENOTE
@bot.slash_command(name="removenote", description="Remove a moderation note from a user (SO+)")
@option("noteid", description="Write the number of the note to be removed")
async def removenote(ctx, noteid: int):
    if check_permissions(ctx.author, ["Senior Officer"]):
        try:
        db_manager.remove_note(noteid)
        await ctx.respond(f"Note with ID {noteid} has been removed.", ephemeral=True)
    except sqlite3.Error as e:
        await ctx.respond(f"Error removing note: {e}", ephemeral=True)
        return

    
	await ctx.defer(ephemeral=True)
        await ctx.followup.send("This command is only available for Senior Officers or higher.")