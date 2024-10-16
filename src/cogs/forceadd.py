from asyncio import timeout

import discord
from discord.ext import commands
from discord import app_commands

from src.config import BOA_NSC
from src.data.repository.sailor_repository import SailorRepository
from logging import getLogger

log = getLogger(__name__)


class ForceAdd(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot


    @app_commands.command(name="forceadd", description="Force-add voyages and/or subclass points to a user (BOA only)")
    @app_commands.describe(target="Select the user to forceadd data to")
    @app_commands.describe(voyages="Add to total voyages. Note: Hosted voyages added separately.")
    @app_commands.describe(hosted="Add to hosted voyages. Note: Total voyages added separately.")
    @app_commands.describe(carpenter="Add carpenter subclass points.")
    @app_commands.describe(cannoneer="Add cannoneer subclass points.")
    @app_commands.describe(flex="Add flex subclass points.")
    @app_commands.describe(helm="Add helm subclass points.")
    @app_commands.describe(surgeon="Add surgeon subclass points.")
    @app_commands.describe(grenardier="Add grenadier subclass points.")
    @app_commands.checks.has_any_role(*BOA_NSC)
    async def forceadd(self, interaction: discord.Interaction, target: discord.Member = None,
                       voyages: int = 0, hosted: int = 0,
                       carpenter: int = 0, cannoneer: int = 0, flex: int = 0, helm: int = 0,
                       surgeon: int = 0, grenardier: int = 0):
        # Quick exit if no target or note is provided
        if target is None:
            await interaction.followup.send("You didn't add a target.")
            return
        
        
        sailor_repo = SailorRepository()
        try:
            # Get sailor
            tgt = sailor_repo.get_sailor(target.id)

            # Apply force values
            tgt.force_voyage_count += voyages
            tgt.force_hosted_count += hosted
            tgt.force_carpenter_points += carpenter
            tgt.force_carpenter_points += cannoneer
            tgt.force_flex_points += flex
            tgt.force_helm_points += helm
            tgt.force_surgeon_points += surgeon
            tgt.force_grenadier_points += grenardier
        except Exception as e:
            await interaction.response.send_message("An error occurred while force adding. Please try again later.", ephemeral=True)
            log.error(f"Failed to force add: {e}")
        finally:
            sailor_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(ForceAdd(bot))
