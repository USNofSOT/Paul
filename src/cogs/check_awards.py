from logging import getLogger
from typing import Union

import discord
from discord.ext import commands
from discord import app_commands

from config import GUILD_ID, MEDALS_AND_RIBBONS, MAX_MESSAGE_LENGTH
from data.repository.sailor_repository import SailorRepository

from src.utils.check_awards import check_sailor

log = getLogger(__name__)


class CheckAwards(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="check_awards", description="Check awards eligibility for a target role")
    @app_commands.describe(target="Mention the role to get awards for")
    async def check_awards(self, interaction: discord.Interaction, target: Union[discord.Member, discord.Role]):
        await interaction.response.defer(ephemeral=True)

        # Check if role is defined
        if isinstance(target, discord.Role):
            members = target.members
            log.info(f"Checking awards for {target.name} with {len(members)} members")
        else:
            members = [target]
            log.info(f"Checking awards for {target.name}")

        # Get the repositories
        sailor_repo = SailorRepository()

        try:
            role_has_sailors = False
            msg_str = ""
            for member in members:
                if isinstance(target, discord.Role):
                    log.info(f"Checking member {member.name}")
                # Check if member in database
                sailor = sailor_repo.get_sailor(member.id)
                if sailor is None:
                    continue
                else:
                    role_has_sailors = True

                # Check for award messages for sailor
                sailor_strs = check_sailor(self.bot, interaction, sailor, member)
                # Add strings to message, printing early if message would be too long
                for sailor_str in sailor_strs:
                    if len(msg_str+sailor_str) <= MAX_MESSAGE_LENGTH:
                        msg_str += sailor_str
                    else:
                        await interaction.followup.send(msg_str, ephemeral=True)
                        msg_str = sailor_str

            if not role_has_sailors:
                msg_str = "Role has no sailors in it"
            elif not msg_str:
                msg_str = "All sailors are up-to-date on awards."
            await interaction.followup.send(msg_str, ephemeral=True)

        except Exception as e:
            log.error(f"Error checking awards: {e}",exc_info=True)
            await interaction.followup.send("Error checking awards", ephemeral=True)

        finally:
            sailor_repo.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(CheckAwards(bot))
