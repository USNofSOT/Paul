import datetime
import discord
from discord.ext import commands
from discord import app_commands
from logging import getLogger

from src.config import SNCO_AND_UP
from src.data import ModNotes
from src.data.repository.modnote_repository import ModNoteRepository
from src.utils.embeds import error_embed, default_embed

log = getLogger(__name__)


class LeaveOfAbsence(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="loa", description="Change a sailor's LOA status (set to 0 for returns). Also used for extensions")
    @app_commands.describe(message_id="Message ID of the LOA post")
    @app_commands.describe(target="Sailor who's LOA status you're changing")
    @app_commands.describe(level="LOA level, 0 being returned to active duty")
    @app_commands.describe(end_date="Return date for LOA in YYYY-MM-DD format. This input is ignored for returning to active duty")
    @app_commands.checks.has_any_role(*SNCO_AND_UP)
    async def loa(self, interaction: discord.interactions, message_id: str, target: discord.Member, level: int, end_date: str):
        await interaction.response.defer (ephemeral=True)

        #######################################################################
        # Input Checks
        #######################################################################

        # Interaction
        ######################
        # Check the interaction member is above target in the chain of command

        # Exceptions to the CoC rule:
        # - Ship CO+ can change their own LOA status
        # - BOA can change any other BOA member's status

        # Message ID
        ######################
        # Check the message is in the leave of absence channel

        # Target
        ######################
        # Check the target is E-2+

        # Level
        ######################
        # Check the level is 0, 1, or 2

        # Exception for AOTN

        # End Date
        ######################
        # Check that input str resolves to valid datetime

        #######################################################################
        # Determine New Nickname
        #######################################################################


        #######################################################################
        # Apply New Nickname
        #######################################################################


        #######################################################################
        # Save Action to Database
        #######################################################################

        
        #######################################################################
        # Write Output Message
        #######################################################################


async def setup(bot: commands.Bot):
    await bot.add_cog(LeaveOfAbsence(bot))
