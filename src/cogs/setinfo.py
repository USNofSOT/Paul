import discord
from discord.ext import commands
from discord import app_commands, Embed

from src.config import SNCO_AND_UP, JE_AND_UP
from src.data import Sailor
from src.data.repository.sailor_repository import SailorRepository
from src.utils.embeds import error_embed, default_embed


class SetInfo(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @app_commands.command(name="setinfo", description="Set your Gamertag or Timezone")
    @app_commands.describe(gamertag="Enter the user's in-game username")
    @app_commands.checks.has_any_role(*JE_AND_UP)
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
    async def setinfo(self, interaction: discord.interactions, gamertag: str = None, timezone: str = None):
        await interaction.response.defer (ephemeral=True)

        # Quick exit if no gamertag or timezone is provided
        if gamertag is None and timezone is None:
            await interaction.followup.send("You didn't add any information.")
            return

        # Attempt to add the information to the database
        # This function will create a new Sailor if one does not exist
        # Ad will not alter gamertag or timezone if None is provided
        try:
            sailor : Sailor = SailorRepository().update_or_create_sailor_by_discord_id(interaction.user.id, gamertag, timezone)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Failed to add information. Please try again.", e))
            return

        if sailor:
            sailor_embed = default_embed(title="Information Added", description=f"Displaying current information for {interaction.user.mention}")
            sailor_embed.add_field(name="Gamertag", value=sailor.gamertag if sailor.gamertag else "Not Set")
            sailor_embed.add_field(name="Timezone", value=sailor.timezone if sailor.timezone else "Not Set")
            await interaction.followup.send(embed=sailor_embed)
        else:
            await interaction.followup.send(embed=error_embed("Failed to add information. Please try again."))

async def setup(bot: commands.Bot):
    await bot.add_cog(SetInfo(bot))  # Classname(bot)