from logging import getLogger

import discord
from discord import app_commands
from discord.ext import commands

from src.config import BOA_NSC
from src.data import SubclassType, Sailor
from src.data.repository.forceadd_repository import save_forceadd
from src.data.repository.sailor_repository import SailorRepository
from src.utils.discord_utils import get_best_display_name
from src.utils.embeds import error_embed, default_embed

log = getLogger(__name__)


class ForceAdd(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    def display_modifier(self, increment: int | None) -> str:
        if increment is None or increment == 0:
            return ""
        return f"+ {increment}" if increment > 0 else f"{increment}"

    def display_bracketed_modifier(self, increment: int | None) -> str:
        if increment is None:
            return ""
        return f"({self.display_modifier(increment)})"

    def get_int(self, increment: int | None) -> int:
        return 0 if increment is None else increment

    def display_int(self, increment: int | None) -> str:
        return "0" if increment is None else str(increment)

    def force_add_report_embed(self, member: discord.Member, force_voyages: int = None, force_hosted: int = None,
                               force_carpenter: int = None, force_cannoneer: int = None, force_flex: int = None,
                               force_helm: int = None, force_surgeon: int = None, force_grenadier: int = None):
        sailor_repo = SailorRepository()
        embed = default_embed(title=f"Displaying force add points for {get_best_display_name(self.bot, member.id)}",
            description=f"Summary of current point counts for {member.mention}")

        sailor: Sailor = sailor_repo.get_sailor(member.id)
        if sailor is None:
            log.error(f"Failed to get sailor for {member.id}")
            return error_embed("Failed to get sailor data. Please try again.")

        embed.add_field(name="Type", value="Voyages"
                                           "\nHosted"
                                           "\nCarpenter"
                                           "\nCannoneer"
                                           "\nFlex"
                                           "\nHelm"
                                           "\nSurgeon"
                                           "\nGrenadier")
        embed.add_field(name="Modifier", value=f"{sailor.force_voyage_count} {self.display_bracketed_modifier(force_voyages)}"
                                               f"\n {sailor.force_hosted_count} {self.display_bracketed_modifier(force_hosted)}"
                                               f"\n {sailor.force_carpenter_points} {self.display_bracketed_modifier(force_carpenter)}"
                                               f"\n {sailor.force_cannoneer_points} {self.display_bracketed_modifier(force_cannoneer)}"
                                               f"\n {sailor.force_flex_points} {self.display_bracketed_modifier(force_flex)}"
                                               f"\n {sailor.force_helm_points} {self.display_bracketed_modifier(force_helm)}"
                                               f"\n {sailor.force_surgeon_points} {self.display_bracketed_modifier(force_surgeon)}"
                                               f"\n {sailor.force_grenadier_points} {str(self.display_bracketed_modifier(force_grenadier))}")
        embed.add_field(name="Result (total + modifier)", value=f"{self.display_int(sailor.voyage_count)} {self.display_modifier(sailor.force_voyage_count)} = {self.display_int(sailor.voyage_count + sailor.force_voyage_count)}"
                                                                f"\n {self.display_int(sailor.hosted_count)} {self.display_modifier(sailor.force_hosted_count)} = {self.display_int(sailor.hosted_count + sailor.force_hosted_count)}"
                                                                f"\n {self.display_int(sailor.carpenter_points)} {self.display_modifier(sailor.force_carpenter_points)} = {self.display_int(sailor.carpenter_points + sailor.force_carpenter_points)}"
                                                                f"\n {self.display_int(sailor.cannoneer_points)} {self.display_modifier(sailor.force_cannoneer_points)} = {self.display_int(sailor.cannoneer_points + sailor.force_cannoneer_points)}"
                                                                f"\n {self.display_int(sailor.flex_points)} {self.display_modifier(sailor.force_flex_points)} = {self.display_int(sailor.flex_points + sailor.force_flex_points)}"
                                                                f"\n {self.display_int(sailor.helm_points)} {self.display_modifier(sailor.force_helm_points)} = {self.display_int(sailor.helm_points + sailor.force_helm_points)}"
                                                                f"\n {self.display_int(sailor.surgeon_points)} {self.display_modifier(sailor.force_surgeon_points)} = {self.display_int(sailor.surgeon_points + sailor.force_surgeon_points)}"
                                                                f"\n {self.display_int(sailor.grenadier_points)} {self.display_modifier(sailor.force_grenadier_points)} = {self.display_int(sailor.grenadier_points + sailor.force_grenadier_points)}")
        sailor_repo.close_session()
        return embed

    @app_commands.command(name="forceadd", description="Force-add voyages and/or subclass points to a user (BOA only)")
    @app_commands.describe(target="Select the user to forceadd data to")
    @app_commands.describe(voyages="Add to total voyages. Note: Hosted voyages added separately.")
    @app_commands.describe(hosted="Add to hosted voyages. Note: Total voyages added separately.")
    @app_commands.describe(carpenter="Add carpenter subclass points.")
    @app_commands.describe(cannoneer="Add cannoneer subclass points.")
    @app_commands.describe(flex="Add flex subclass points.")
    @app_commands.describe(helm="Add helm subclass points.")
    @app_commands.describe(surgeon="Add surgeon subclass points.")
    @app_commands.describe(grenadier="Add grenadier subclass points.")
    @app_commands.checks.has_any_role(*BOA_NSC)
    async def forceadd(self, interaction: discord.Interaction, target: discord.Member = None, voyages: int = None,
                       hosted: int = None, carpenter: int = None, cannoneer: int = None, flex: int = None,
                       helm: int = None, surgeon: int = None, grenadier: int = None):
        await interaction.response.defer(ephemeral=True)

        # Quick exit if no target or note is provided
        if target is None:
            await interaction.followup.send(embed=error_embed(title="No Target Provided",
                description="Please provide a target to force add data to."))
            return

        # If no values to increment or decrement are provided, display current values
        if voyages is None and hosted is None and carpenter is None and cannoneer is None and flex is None and helm is None and surgeon is None and grenadier is None:
            await interaction.followup.send(embed=self.force_add_report_embed(target))
            return

        sailor_repo = SailorRepository()
        try:
            # Apply force values
            tgt_id = target.id
            if voyages is not None:
                sailor_repo.increment_force_voyage_by_discord_id(tgt_id, voyages)
                save_forceadd(
                    target_id=tgt_id,
                    type="voyages",
                    amount=voyages,
                    moderator_id=interaction.user.id
                )
            if hosted is not None:
                sailor_repo.increment_force_hosted_by_discord_id(tgt_id, hosted)
                save_forceadd(
                    target_id=tgt_id,
                    type="hosted",
                    amount=hosted,
                    moderator_id=interaction.user.id
                )
            if carpenter is not None:
                sailor_repo.increment_force_subclass_by_discord_id(tgt_id, SubclassType.CARPENTER, carpenter)
                save_forceadd(
                    target_id=tgt_id,
                    type="carpenter",
                    amount=carpenter,
                    moderator_id=interaction.user.id
                )
            if cannoneer is not None:
                sailor_repo.increment_force_subclass_by_discord_id(tgt_id, SubclassType.CANNONEER, cannoneer)
                save_forceadd(
                    target_id=tgt_id,
                    type="cannoneer",
                    amount=cannoneer,
                    moderator_id=interaction.user.id
                )
            if flex is not None:
                sailor_repo.increment_force_subclass_by_discord_id(tgt_id, SubclassType.FLEX, flex)
                save_forceadd(
                    target_id=tgt_id,
                    type="flex",
                    amount=flex,
                    moderator_id=interaction.user.id
                )
            if helm is not None:
                sailor_repo.increment_force_subclass_by_discord_id(tgt_id, SubclassType.HELM, helm)
                save_forceadd(
                    target_id=tgt_id,
                    type="helm",
                    amount=helm,
                    moderator_id=interaction.user.id
                )
            if surgeon is not None:
                sailor_repo.increment_force_subclass_by_discord_id(tgt_id, SubclassType.SURGEON, surgeon)
                save_forceadd(
                    target_id=tgt_id,
                    type="surgeon",
                    amount=surgeon,
                    moderator_id=interaction.user.id
                )
            if grenadier is not None:
                sailor_repo.increment_force_subclass_by_discord_id(tgt_id, SubclassType.GRENADIER, grenadier)
                save_forceadd(
                    target_id=tgt_id,
                    type="grenadier",
                    amount=grenadier,
                    moderator_id=interaction.user.id
                )

            await interaction.followup.send(embed=self.force_add_report_embed(target, voyages, hosted, carpenter, cannoneer, flex, helm, surgeon, grenadier))
        except Exception as e:
            await interaction.followup.send(embed=error_embed("Failed to force add. Please try again."))
            log.error(f"Failed to force add: {e}")
        finally:
            sailor_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(ForceAdd(bot))
