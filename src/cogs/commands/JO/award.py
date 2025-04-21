import discord
from config import JO_AND_UP, awards_repository
from data.model.award_recipients_model import AwardRecipients
from data.model.awards_model import Awards
from data.repository.award_recipients_repository import AwardRecipientsRepository
from data.repository.awards_repository import AwardsRepository
from discord import app_commands
from discord.ext import commands
from utils.embeds import error_embed
from utils.time_utils import utc_time_now


async def autocomplete_award(
    interaction: discord.Interaction,
    current_input: str,
) -> list[app_commands.Choice]:
    repository = AwardsRepository()
    choices = []
    for award in repository.find(
        filters={
            "is_awardable": True,  # Only show awards that are awardable
            "role_id": None,  # Only show awards that are not role awards
        }
    ):
        if current_input == "":
            choices.append(app_commands.Choice(name=award.name, value=award.name))
        elif award.name.lower().startswith(current_input.lower()):
            choices.append(app_commands.Choice(name=award.name, value=award.name))
    awards_repository.close_session()
    return choices[:25]


class AwardCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def assign_award(self, target: discord.Member, award: Awards):
        pass

    @app_commands.command(name="award")
    @app_commands.describe(target="Select the user you want to alter the award for")
    @app_commands.choices(
        action=[
            app_commands.Choice(name="Assign", value="assign"),
            app_commands.Choice(name="Remove", value="remove"),
        ]
    )
    @app_commands.describe(action="Select the action you want to perform")
    @app_commands.autocomplete(award=autocomplete_award)
    @app_commands.describe(award="Select the award you want to perform the action on")
    @app_commands.checks.has_any_role(*JO_AND_UP)
    async def award(
        self,
        interaction: discord.Interaction,
        target: discord.Member,
        action: str,
        award: str,
    ):
        # Await the response
        await interaction.response.defer(ephemeral=True)

        # If target is None, set target to the author of the interaction
        if target is None:
            target = interaction.user

        # 1. Validate input
        # 1.1 Check if the action is valid
        if action not in ["assign", "remove"]:
            await interaction.followup.send(
                embed=error_embed("Invalid action", "Please select a valid action.")
            )
            return
        # 1.2 Check if the award is valid
        repository = AwardsRepository()
        award = repository.find_by_name(award)
        if award is None:
            await interaction.followup.send(
                embed=error_embed("Invalid award", "Please select a valid award.")
            )
            return
        repository.close_session()

        embed = None

        # 2. Perform the action
        if action == "assign":
            embed = assign_award(target, interaction.user, award)
        elif action == "remove":
            embed = remove_award(target, interaction.user, award)

        # 3. Send the response
        # 3.1 If embed is None, send an error embed
        if embed is None:
            embed = error_embed(
                "Something went wrong",
                "An error occurred while performing the action.",
            )
        # 3.2 Send the embed
        await interaction.followup.send(embed=embed)


def assign_award(target: discord.Member, moderator: discord.Member, award: Awards):
    if not award.is_awardable:
        return error_embed(
            "Award not awardable",
            f"The **{award.name}** award is not awardable.",
            footer=False,
        )

    repository = AwardRecipientsRepository()
    if repository.find({"target_id": target.id, "award_id": award.id}):
        return error_embed(
            "Award already assigned",
            f"{target.display_name} already has the **{award.name}** award.",
            footer=False,
        )

    embed = discord.Embed(
        title=f"**{award.name}** successfully assigned to {target.display_name}",
        description=f"{award.description}",
        color=discord.Color.green(),
    )
    embed.add_field(name="Awarded by", value=f"{moderator.display_name}", inline=True)
    embed.add_field(
        name="Awarded on",
        value=f"{utc_time_now().strftime('%Y-%m-%d %H:%M:%S')}",
        inline=True,
    )
    try:
        repository.create(
            AwardRecipients(
                target_id=target.id,
                award_id=award.id,
                moderator_id=moderator.id,
                created_at=utc_time_now(),
            )
        )
    except Exception as e:
        repository.rollback()
        raise e
    finally:
        repository.close_session()
    return embed


def remove_award(target: discord.Member, moderator: discord.Member, award: Awards):
    repository = AwardRecipientsRepository()
    recipient = repository.find({"target_id": target.id, "award_id": award.id})
    if not recipient:
        return error_embed(
            "Award not assigned",
            f"{target.display_name} does not have the **{award.name}** award.",
            footer=False,
        )

    embed = discord.Embed(
        title=f"**{award.name}** successfully removed from {target.display_name}",
        description=f"{award.description}",
        color=discord.Color.green(),
    )
    embed.add_field(name="Removed by", value=f"{moderator.display_name}", inline=True)
    embed.add_field(
        name="Removed on",
        value=f"{utc_time_now().strftime('%Y-%m-%d %H:%M:%S')}",
        inline=True,
    )
    try:
        repository.remove(recipient[0])
    except Exception as e:
        repository.rollback()
        raise e
    finally:
        repository.close_session()
    return embed


async def setup(bot):
    await bot.add_cog(AwardCommand(bot))
