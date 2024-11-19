import logging
from dbm import error

import discord
from discord import app_commands
from discord.ext import commands

from src.config.ranks_roles import BOA_ROLE, NCO_AND_UP
from src.data.repository.sailor_repository import SailorRepository
from src.utils.embeds import error_embed, default_embed

log = logging.getLogger(__name__)

class Gamertags(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="gamertags", description="Get the gamertags of all users in the voice channel of the executing user")
    @app_commands.describe(target="Select a role to get the gamertags of all users in the voice channel of the executing user")
    @app_commands.checks.has_any_role(*NCO_AND_UP)
    async def gamertags(self, interaction: discord.Interaction, target: discord.Role = None):
        """
        Get the gamertags of all users in the voice channel of the executing user.
        """
        if target:
            if len(target.members) > 30:
                await interaction.response.send_message(embed=error_embed(title="Error", description="Too many members with the selected role."), ephemeral=True)
                return

            embed = default_embed(title="Gamertags overview",
                                  description=f"The gamertags of all users with the role {target.mention}")
            user_strings = ""
            sailor_repository = SailorRepository()
            for member in target.members:
                sailor = sailor_repository.get_sailor(member.id)
                if sailor is not None and sailor.gamertag is not None:
                    user_strings += f"- <@{member.id}>: {sailor.gamertag}\n"
                else:
                    user_strings += f"- <@{member.id}>: No gamertag set\n"

            embed.add_field(name="Gamertags", value=user_strings)
            await interaction.response.send_message(embed=embed)
            sailor_repository.close_session()
            return


        member = interaction.user

        if member.voice is None:
            await interaction.response.send_message(embed=error_embed(title="Not in VC", description="You have to be in a voice channel to use this command."), ephemeral=True)
            return
        voice_channel = member.voice.channel
        if voice_channel is None:
            await interaction.response.send_message(embed=error_embed(title="Not in VC", description="You have to be in a voice channel to use this command."), ephemeral=True)
            return

        members = voice_channel.members

        voice_channel_url = f"https://discord.com/channels/{voice_channel.guild.id}/{voice_channel.id}"

        if not members:
            await interaction.response.send_message(embed=error_embed(title="Error", description="There are no members in the voice channel."), ephemeral=True)
            return

        embed = default_embed(title="Gamertags overview", description=f"The gamertags of all users in {voice_channel_url}")
        user_strings = ""
        sailor_repository = SailorRepository()
        for member in members:
            sailor = sailor_repository.get_sailor(member.id)
            if sailor is not None and sailor.gamertag is not None:
                user_strings += f"- <@{member.id}>: {sailor.gamertag}\n"
            else:
                user_strings += f"- <@{member.id}>: No gamertag set\n"

        embed.add_field(name="Gamertags", value=user_strings)
        await interaction.response.send_message(embed=embed)

        sailor_repository.close_session()

    @gamertags.error
    async def gamertags_error(self, interaction: discord.Interaction, exception: commands.CommandError):
        if isinstance(exception, app_commands.errors.MissingAnyRole):
            await interaction.response.send_message(embed=error_embed(title="Missing Permissions", description="You do not have the required permissions to execute this command."))
        else:
            log.error(f"An error occurred in the gamertags command: {error}")
            await interaction.response.send_message(embed=error_embed(title="An Error Occurred", description="An error occurred while executing this command. Please try again later.", exception=exception))

async def setup(bot: commands.Bot):
    await bot.add_cog(Gamertags(bot))
