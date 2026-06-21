import logging

import discord
from discord import app_commands
from discord.ext import commands
from sqlalchemy.orm import Session

from src.data import Sailor
from src.data.repository.sailor_repository import SailorRepository
from src.security import require_any_role, audit_interaction, Role
from src.utils.embeds import error_embed, default_embed

log = logging.getLogger(__name__)

class AddInfo(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def get_sailor_attached(self, session: Session, sailor_or_id):
        """Return a Sailor instance bound to `session` (accepts Sailor or discord_id)."""
        sailor_id = getattr(sailor_or_id, "discord_id", sailor_or_id)
        return session.get(Sailor, sailor_id)

    @app_commands.command(name="addinfo", description="Add Gamertag or Timezone to yourself or another user")
    @app_commands.describe(target="Select the user to add information to")
    @app_commands.describe(gamertag="Enter the user's in-game username")
    @require_any_role(Role.SNCO, Role.NRC)
    @audit_interaction
    @app_commands.choices(timezone=[
                                    app_commands.Choice(name="Niue Time, Samoa Standard Time - UTC-11:00 (NUT)", value="UTC-11:00 (NUT)"),
                                    app_commands.Choice(name="Hawaii-Aleutian Standard Time - UTC-10:00 (HST)", value="UTC-10:00 (HST)"),
                                    app_commands.Choice(name="Alaska Standard Time - UTC-09:00 (AKST)", value="UTC-09:00 (AKST)"),
                                    app_commands.Choice(name="Pacific Standard Time - UTC-08:00 (PST)", value="UTC-08:00 (PST)"),
                                    app_commands.Choice(name="Mountain Standard Time - UTC-07:00 (MST)", value="UTC-07:00 (MST)"),
                                    app_commands.Choice(name="Central Standard Time - UTC-06:00 (CST)", value="UTC-06:00 (CST)"),
                                    app_commands.Choice(name="Eastern Standard Time - UTC-05:00 (EST)", value="UTC-05:00 (EST)"),
                                    app_commands.Choice(name="Atlantic Standard Time - UTC-04:00 (AST)", value="UTC-04:00 (AST)"),
                                    app_commands.Choice(name="Brasilia Time, Argentina Standard Time - UTC-03:00 (BRT)", value="UTC-03:00 (BRT)"),
                                    app_commands.Choice(name="Fernando de Noronha Time - UTC-02:00 (FNT)", value="UTC-02:00 (FNT)"),
                                    app_commands.Choice(name="Cape Verde Time, Azores Standard Time - UTC-01:00 (CVT)", value="UTC-01:00 (CVT)"),
                                    app_commands.Choice(name="Coordinated Universal Time, Greenwich Mean Time - UTC±00:00 (UTC)", value="UTC±00:00 (UTC)"),
                                    app_commands.Choice(name="Central European Time, West Africa Time - UTC+01:00 (CET)", value="UTC+01:00 (CET)"),
                                    app_commands.Choice(name="Eastern European Time, Central Africa Time - UTC+02:00 (EET)", value="UTC+02:00 (EET)"),
                                    app_commands.Choice(name="Moscow Time, East Africa Time - UTC+03:00 (MSK)", value="UTC+03:00 (MSK)"),
                                    app_commands.Choice(name="Gulf Standard Time, Samara Time - UTC+04:00 (GST)", value="UTC+04:00 (GST)"),
                                    app_commands.Choice(name="Pakistan Standard Time, Yekaterinburg Time - UTC+05:00 (PKT)", value="UTC+05:00 (PKT)"),
                                    app_commands.Choice(name="Bangladesh Standard Time, Omsk Time - UTC+06:00 (BST)", value="UTC+06:00 (BST)"),
                                    app_commands.Choice(name="Indochina Time, Krasnoyarsk Time - UTC+07:00 (ICT)", value="UTC+07:00 (ICT)"),
                                    app_commands.Choice(name="China Standard Time, Australian Western Standard Time - UTC+08:00 (CST)", value="UTC+08:00 (CST)"),
                                    app_commands.Choice(name="Japan Standard Time, Korea Standard Time - UTC+09:00 (JST)", value="UTC+09:00 (JST)"),
                                    app_commands.Choice(name="Australian Eastern Standard Time - UTC+10:00 (AEST)", value="UTC+10:00 (AEST)"),
                                    app_commands.Choice(name="Vladivostok Time, Solomon Islands Time - UTC+11:00 (VLAT)", value="UTC+11:00 (VLAT)"),
                                    app_commands.Choice(name="New Zealand Standard Time, Fiji Time - UTC+12:00 (NZST)", value="UTC+12:00 (NZST)"),
                                    app_commands.Choice(name="International Date Line West - UTC-12:00 (IDLW)", value="UTC-12:00 (IDLW)")
                                ])
    async def addinfo(self, interaction: discord.Interaction, target: discord.Member = None, gamertag: str = None,
                      timezone: str = None):
        await interaction.response.defer(ephemeral=True)

        # Quick exit if no gamertag or timezone is provided
        if gamertag is None and timezone is None:
            await interaction.followup.send("You didn't add any information.")
            return

        # Set the target to the user if not provided
        if target is None:
            target = interaction.user

        try:
            with SailorRepository() as repo:
                # Use the repository's session
                session = repo.session
                sailor = self.get_sailor_attached(session, target.id)

                if not sailor:
                    # Create a new sailor if one doesn't exist
                    sailor = Sailor(discord_id=target.id)
                    session.add(sailor)

                if gamertag:
                    sailor.gamertag = gamertag
                if timezone:
                    sailor.timezone = timezone

                session.commit()

                # Capture values while session is active
                current_gamertag = sailor.gamertag
                current_timezone = sailor.timezone

            sailor_embed = default_embed(title="Information Added",
                                         description=f"Displaying current information for {target.mention}")
            sailor_embed.add_field(name="Gamertag", value=current_gamertag if current_gamertag else "Not Set")
            sailor_embed.add_field(name="Timezone", value=current_timezone if current_timezone else "Not Set")
            await interaction.followup.send(embed=sailor_embed)
            
        except Exception as e:
            log.error(f"Error in addinfo command: {e}", exc_info=True)
            await interaction.followup.send(embed=error_embed("Failed to add information. Please try again.", exception=e))

async def setup(bot: commands.Bot):
    await bot.add_cog(AddInfo(bot))
