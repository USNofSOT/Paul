import discord
from discord.ext import commands
from discord import app_commands

from src.config import BOA_NSC
from src.data import SubclassType
from src.data.repository.sailor_repository import SailorRepository, save_sailor
from src.utils.embeds import error_embed, default_embed
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
                       surgeon: int = 0, grenadier: int = 0):
        await interaction.response.defer (ephemeral=True)

        # Quick exit if no target or note is provided
        if target is None:
            await interaction.followup.send("You didn't add a target.")
            return
        
        
        sailor_repo = SailorRepository()
        try:
            # Apply force values
            tgt_id = target.id
            sailor_repo.increment_force_voyage_by_discord_id(tgt_id, voyages)
            sailor_repo.increment_force_hosted_by_discord_id(tgt_id, hosted)
            sailor_repo.increment_force_subclass_by_discord_id(tgt_id,SubclassType.CARPENTER, carpenter)
            sailor_repo.increment_force_subclass_by_discord_id(tgt_id,SubclassType.CANNONEER, cannoneer)
            sailor_repo.increment_force_subclass_by_discord_id(tgt_id,SubclassType.FLEX, flex)
            sailor_repo.increment_force_subclass_by_discord_id(tgt_id,SubclassType.HELM, helm)
            sailor_repo.increment_force_subclass_by_discord_id(tgt_id,SubclassType.SURGEON, surgeon)
            sailor_repo.increment_force_subclass_by_discord_id(tgt_id, SubclassType.GRENADIER, grenadier)

            # Print applied values
            tgt = sailor_repo.get_sailor(target.id)
            force_embed = default_embed(title="Force Added Values", description=f"Displaying current force values for {target.mention}")
            force_embed.add_field(name="Voyages", value=tgt.force_voyage_count)
            force_embed.add_field(name="Hosted", value=tgt.force_hosted_count)
            force_embed.add_field(name="Carpenter", value=tgt.force_carpenter_points)
            force_embed.add_field(name="Cannoneer", value=tgt.force_cannoneer_points)
            force_embed.add_field(name="Flex", value=tgt.force_flex_points)
            force_embed.add_field(name="Helm", value=tgt.force_helm_points)
            force_embed.add_field(name="Surgeon", value=tgt.force_surgeon_points)
            force_embed.add_field(name="Grenardier", value=tgt.force_grenadier_points)
            await interaction.followup.send(embed=force_embed)
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Failed to force add. Please try again."))
            log.error(f"Failed to force add: {e}")
        finally:
            sailor_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(ForceAdd(bot))
