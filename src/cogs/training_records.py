import discord
from discord import app_commands
from discord.ext import commands

from src.config import JE_AND_UP, NETC_GUILD_ID, JLA_INSTRUCTOR_ROLE, SNLA_INSTRUCTOR_ROLE, OCS_GRADUATE_ROLE, \
    SOCS_GRADUATE_ROLE, OCS_INSTRUCTOR_ROLE, SOCS_INSTRUCTOR_ROLE
from src.data import TrainingRecord
from src.data.repository.training_records_repository import TrainingRecordsRepository
from src.utils.embeds import default_embed
from src.utils.time_utils import format_time, get_time_difference_past


class TrainingRecords(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="trainingrecords", description="Get information about a members training records")
    @app_commands.describe(target="Select the user you want to get information about")
    @app_commands.checks.has_any_role(*JE_AND_UP)
    async def training_records(self, interaction: discord.interactions, target: discord.Member = None):
        if target is None:
            target = interaction.user

        # Get the training records of the target
        training_repository = TrainingRecordsRepository()
        training_record: TrainingRecord = training_repository.get_or_create_training_record(target.id)
        training_repository.close_session()

        embed = default_embed(
            title=f"Training Records",
            description=f"{target.mention}",
            author=False
        )

        # Attempt to set the thumbnail to the target's avatar
        try:
            avatar_url = target.guild_avatar.url if target.guild_avatar else target.avatar.url
            embed.set_thumbnail(url=avatar_url)
        except AttributeError:
            pass

        embed.add_field(
            name="Total Training Points",
            value=f"{training_record.nrc_training_points+training_record.netc_training_points}",
            inline=True
        )
        embed.add_field(
            name="Total NRC Points",
            value=f"{training_record.nrc_training_points}",
            inline=True
        )
        embed.add_field(
            name="Total NETC Points",
            value=f"{training_record.netc_training_points}",
            inline=True
        )

        netc_member = self.bot.get_guild(NETC_GUILD_ID).get_member(target.id)
        if not netc_member is None:
            netc_member_roles = [role.id for role in netc_member.roles]
            if JLA_INSTRUCTOR_ROLE in netc_member_roles:
                embed.add_field(
                    name="Total JLA Points",
                    value=f"{training_record.jla_training_points}",
                    inline=True
                )
            if SNLA_INSTRUCTOR_ROLE in netc_member_roles:
                embed.add_field(
                    name="Total SNLA Training Points",
                    value=f"{training_record.snla_training_points}",
                    inline=True
                )
            if OCS_INSTRUCTOR_ROLE in netc_member_roles:
                embed.add_field(
                    name="Total OCS Training Points",
                    value=f"{training_record.ocs_training_points}",
                    inline=True
                )
            if SOCS_INSTRUCTOR_ROLE in netc_member_roles:
                embed.add_field(
                    name="Total SOCS Training Points",
                    value=f"{training_record.socs_training_points}",
                    inline=True
                )

        # for record in [
        #     ("JLA", training_records.jla_graduation_date),
        #     ("SNLA", training_records.snla_graduation_date),
        #     ("OCS", training_records.ocs_graduation_date),
        #     ("SOCS", training_records.socs_graduation_date)
        # ]:
        #     name, date = record
        #     embed.add_field(
        #         name=name,
        #         value=f"Graduated for {name} since {format_time(get_time_difference_past(date))}" if date else "Not graduated",
        #         inline=False
        #     )

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TrainingRecords(bot))