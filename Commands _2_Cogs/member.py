#member command
@bot.tree.command(name="member", description="Check information of a user or all users in a role")
@app_commands.describe(target="Choose a user or role to grab info for")
@app_commands.describe(level="Choose info view")
@app_commands.choices(level=[
    app_commands.Choice(name="Default", value="default"),
    app_commands.Choice(name="Moderation", value="moderation"),
    app_commands.Choice(name="Promotion", value="promotion")
])
async def member(interaction: discord.Interaction, target: discord.Member | discord.Role = None, level: str = None):
    # ... your command logic ...
    if target is None
        target = interaction.user


if level is None:
    level = "default"  # Set default level

    if level.lower() == "default"

    if level.lower() == "promotion"

if level.lower() == "moderation":
    allowed_roles = ["Board of Admiralty", "Junior Officer", "Senior Officer",
                     "Senior Non Commissioned Officer"]  # Add other allowed roles here
    if not any(role.name in allowed_roles for role in interaction.user.roles):
        await interaction.response.send_message("You don't have permission to use this level.", ephemeral=True)
        return