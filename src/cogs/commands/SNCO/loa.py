import datetime
import discord
from discord.ext import commands
from discord import app_commands
from logging import getLogger
import re

from src.config import GUILD_ID, LEAVE_OF_ABSENCE, E2_AND_UP, SNCO_AND_UP, SO_AND_UP, BOA_ROLE, AOTN_ROLES
from src.config.ranks import RANKS
from src.data.structs import SailorCO, RankedNickname
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
    async def loa(self, interaction: discord.Interaction, message_id: int, target: discord.Member, level: int, end_date: str):
        await interaction.response.defer (ephemeral=True)

        log.info(f"LOA status change requested by {interaction.user.display_name or interaction.user.name}")
        log.info(f"[INPUT] Message ID: {message_id}")
        log.info(f"[INPUT] Target: {target.display_name or target.name}")
        log.info(f"[INPUT] Level: {level}")
        log.info(f"[INPUT] End Date: {end_date}")

        target_name = target.display_name or target.name
        guild = self.bot.get_guild(GUILD_ID)

        #######################################################################
        # Input Checks
        #######################################################################

        # Interaction
        ######################
        # Check the interaction member is above target in the chain of command
        is_superior = check_superiority(interaction.user, target, guild)
        is_superior = is_superior or CoC_exceptions(interaction.user, target)

        if not is_superior:
            log.info(f"[INPUT ERROR] Interaction member is not above target in CoC (or an exceptional case).")

            descr = f"You are not in the chain of command for {target_name}:"
            while imm_CO := SailorCO(target).immediate:
                descr += f" {imm_CO.display_name or imm_CO.name}"
                target = imm_CO

            embed = error_embed(title="Outside the Chain of Command",
                                description=descr,
                                footer=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Message ID
        ######################
        # Check the message is in the leave of absence channel
        is_in_channel = check_loa_channel(message_id, guild)
        if not is_in_channel:
            log.info(f"[INPUT ERROR] Message ID not in LOA channel.")
            embed = error_embed(title="Invalid Message ID",
                                description=f"Please tag a message in the LOA channel, {guild.get_channel(LEAVE_OF_ABSENCE).name}.",
                                footer=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Target
        ######################
        # Check the target is E-2+
        valid_target_roles = check_loa_target_roles(target)
        if not is_in_channel:
            log.info(f"[INPUT ERROR] Target is not E-2+.")
            embed = error_embed(title="Invalid Target",
                                description=f"Please tag sailor E-2+.",
                                footer=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        # Level
        ######################
        # Check the level is 0, 1, or 2
        # Exception for AOTN
        is_valid_level, err_descr = check_loa_level(level, guild)
        if not is_valid_level:
            log.info(f"[INPUT ERROR] Invalid level value {level}.")
            embed = error_embed(title="Invalid LOA Level",
                                description=descr,
                                footer=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        
        level_currrent = current_loa_level(target)
        if (level == 0) and (level_currrent == 0):
            log.info(f"[INPUT ERROR] Attempting to extend LOA-0.")
            embed = error_embed(title="Invalid LOA Level",
                                description=f"Attempting to set LOA to {level} when it is currently {level_currrent} for an active duty sailor.",
                                footer=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return


        # End Date
        ######################
        # Check that input string resolves to valid datetime
        is_valid_date, end_date_dt = check_loa_end_date(end_date)
        is_valid_date = is_valid_date or (level == 0)  # bypass check if returning from LOA

        if not is_valid_date:
            log.info(f"[INPUT ERROR] Invalid end date value {end_date}.")
            embed = error_embed(title="Invalid End Date",
                                description=f"End date value {end_date} does not follow the YYYY-MM-DD format.",
                                footer=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return

        #######################################################################
        # Nickname Update
        #######################################################################
        try:
            target_ranked_nick = RankedNickname.from_member(target, RANKS)
        except:
            log.info(f"[ERROR] error in generating ranked nickname for target.")
            embed = error_embed(title="Ranked Nickname Generation Error",
                                description="Contact NSC to report the issue.",
                                footer=False)
            await interaction.followup.send(embed=embed, ephemeral=True)
            return
        old_LOA = target_ranked_nick.LOA
        if old_LOA != level:
            target_ranked_nick.LOA = level
            new_nickname = str(target_ranked_nick)
            await target.edit(nick=new_nickname)
            log.info(f"[INFO] New nickname is: {new_nickname}")
        else:
            new_nickname = target_name
            log.info(f"[INFO] No change to nickname.")

        #######################################################################
        # Save Action to Database
        #######################################################################
        target_id = target.id
        changed_by_id = interaction.user.id
        name_before = target_name
        name_after = new_nickname

        loa_before = old_LOA
        loa_after = level
        # end_date_dt previously defined

        # TODO: update/define this
        # loa_repository.save_loa(target_id, changed_by_id, name_before, name_after, loa_before, loa_after, end_date_dt)

        
        #######################################################################
        # Write Output Message
        #######################################################################
        descr = ""
        descr += f"Name: {target_name}\n"
        if loa_before and loa_after:
            loa_str = f"LOA-{loa_before} -> LOA-{loa_after}"
        if loa_before:
            loa_str = f"Returned from LOA-{loa_before}"
        if loa_after:
            loa_str = f"LOA-{loa_after}"
        else:
            loa_str = "No status change"
        descr += f"LOA: {loa_str}\n"
        descr += f"End Date (YYYY-MM-DD): {end_date_dt.strftime("%Y-%m-%d")}\n"
        if new_nickname != target_name:
            descr += f"New Name: {new_nickname}\n"
        descr += f"Changed by: {interaction.user.nick}\n"

        embed = default_embed(title="LOA Status Change Summary",
                              description=descr)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(LeaveOfAbsence(bot))



def check_superiority(superior: discord.Member, subordinate: discord.Member, guild: discord.Guild):
    # Check if first input is superior to the second input
    sub_CO = SailorCO(subordinate, guild).immediate

    # If the subordinate has no CO, then no one can be their CO
    if sub_CO is None:
        return False
    
    # If the superior is their CO, return true.
    # Otherwise, check if the superior is their CO's superior
    if superior == sub_CO:
        return True
    else:
        return check_superiority(superior, sub_CO, guild)


def CoC_exceptions(user: discord.Member, target: discord.Member):
    # Exceptions to the CoC rule:
    # - Ship SO+ can change their own LOA status
    # - BOA can change any member's status

    is_SO_plus = any([role.id in SO_AND_UP for role in user.roles])
    if is_SO_plus and (user == target):
        return True
    
    if any([role.id == BOA_ROLE for role in user.roles]):
        return True
    
    return False


def check_loa_channel(message_id: int, guild: discord.Guild):
    try:
        loa_channel = guild.get_channel(LEAVE_OF_ABSENCE)
        loa_channel.fetch_message(message_id)
    except:
        in_channel = False
    else:
        in_channel = True

    return in_channel


def check_loa_target_roles(target: discord.Member):
    for role in target.roles:
        role_id = role.id
        if role_id in E2_AND_UP:
            return True
    return False


def check_loa_level(level: int, user: discord.Member):
    is_aotn = False
    for role in user.roles:
        if role.id in AOTN_ROLES:
            is_aotn = True
            break
    
    if is_aotn:
        if level >= 0:
            return (True, "")
        return (False, f"Level {level} is not >=0")
    if level in (0, 1, 2):
        return (True, "")
    return (False, f"Level {level} is not 0, 1, or 2.")


def check_loa_end_date(date_str: str):
    try:
        date_parts = [int(part) for part in date_str.split('-')]
        assert len(date_parts) == 3
        end_date_dt = datetime.datetime(*date_parts)
    except:
        valid_str = False
        end_date_dt = datetime.datetime.now()
    else:
        valid_str = True
    return (valid_str, end_date_dt)


def current_loa_level(target: discord.Member):
    # Check if LOA in name
    nickname = target.nick or target.name
    if 'LOA' not in nickname.upper():
        return 0
    
    # Extract LOA level
    level_str = re.search(r"\[LOA-(\d+)\]", nickname)
    return int(level_str)
