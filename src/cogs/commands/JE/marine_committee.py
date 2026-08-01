import discord
from discord import app_commands
from discord.ext import commands

from src.config.ranks_roles import USMC_ROLE
from src.security import Role, require_any_role
from src.utils.embeds import marine_embed

MARINE_COMMANDANT_DISCORD_ID: int | None = 281119159012556800
ASSISTANT_MARINE_COMMANDANT_DISCORD_ID: int | None = None


def _member_mention(discord_id: int | None) -> str:
    if discord_id is None:
        return "N/A"

    return f"<@{discord_id}>"


class MarineCommittee(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="marinecommittee",
        description="View the Marine Committee members.",
    )
    @require_any_role(Role.JE)
    async def marineCommittee(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=False)

        marine_committee_role = interaction.guild.get_role(USMC_ROLE)
        marines = [
            member
            for member in interaction.guild.members
            if marine_committee_role in member.roles
        ]

        embed = marine_embed()
        embed.title = "USMC Committee Members"

        embed.add_field(
            name="__**Marine Commandant**__ ",
            value=_member_mention(MARINE_COMMANDANT_DISCORD_ID),
            inline=False,
        )

        embed.add_field(
            name="__**Assistant Marine Commandant**__ ",
            value=_member_mention(ASSISTANT_MARINE_COMMANDANT_DISCORD_ID),
            inline=False,
        )

        embed.add_field(
            name="__**Marine Committee**__",
            value=(
                    "\n".join(f"{member.mention}" for member in marines)
                or "No members found."
            ),
            inline=False,
        )

        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(MarineCommittee(bot))
