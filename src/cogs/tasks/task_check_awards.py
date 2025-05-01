import datetime
from logging import getLogger
from unittest.mock import MagicMock, AsyncMock

import discord
from discord.ext import commands, tasks
from discord.ext.commands.view import StringView

from src.config import MAX_MESSAGE_LENGTH
from src.config import BOA_ROLE
from src.config.main_server import GUILD_ID, BC_BOA
from src.config.ships import SHIPS
from src.data.repository.sailor_repository import SailorRepository
from src.utils.check_awards import check_sailor
from src.utils.discord_utils import alert_engineers

log = getLogger(__name__)

# Super nasty: reconsider - Trigs
def fake_context(bot, GUILD, channel_name="test-channel"):
    message = MagicMock(spec=discord.Message)
    message.author = MagicMock(spec=discord.User)
    message.channel = MagicMock(spec=discord.TextChannel)
    message.channel.name = channel_name
    ctx = commands.Context(bot=bot, message=message, view=StringView(buffer=""))
    ctx.guild.name = GUILD.name
    ctx.guild.roles = GUILD.roles
    ctx.guild.members = GUILD.members
    ctx.guild.get_member = GUILD.get_member
    ctx.send = AsyncMock()
    return ctx

def create_award_messages(role, sailor_repo, GUILD, context, exclude_roles=[]):
    messages = []
    msg_str = ""
    for member in role.members:
        # Get sailor data
        sailor = sailor_repo.get_sailor(member.id)
        if sailor is None:
            continue
        
        # Skip if member has any excluded roles
        exclude = False
        for ex_role in exclude_roles:
            if ex_role in sailor.roles:
                exclude = True
                break
        if exclude:
            continue

        # Check for award messages for sailor
        sailor_strs = check_sailor(GUILD, context, sailor, member)

        # Add strings to message, printing early if message would be too long
        for sailor_str in sailor_strs:
            if len(msg_str + sailor_str) <= MAX_MESSAGE_LENGTH:
                msg_str += sailor_str
            else:
                messages.append(msg_str)
                msg_str = sailor_str
    if msg_str:
        messages.append(msg_str)
    return messages


class AutoCheckAwards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    # TODO: Move this into configuration as well
    @tasks.loop(time=datetime.time(hour=15, minute=00, tzinfo=datetime.timezone.utc))
    async def my_task(self):
        GUILD = self.bot.get_guild(GUILD_ID)

        sailor_repo = SailorRepository()
        boa_role = GUILD.get_role(BOA_ROLE)
        try:
            # Ship-assigned members
            for ship in SHIPS:
                log.info(f"Checking awards for {ship}")
                channel = GUILD.get_channel(ship.boat_command_channel_id)
                role = GUILD.get_role(ship.role_id)

                context = fake_context(self.bot, GUILD, f"{ship.name}")
                award_msgs = create_award_messages(role, sailor_repo, GUILD, context, exclude_roles=[boa_role])
                for msg_str in award_msgs:
                    await channel.send(msg_str)
            
            # BOA members
            log.info(f"Checking awards for BOA")
            channel = GUILD.get_channel(BC_BOA)
            context = fake_context(self.bot, GUILD, "Board of Admiralty")
            award_msgs = create_award_messages(boa_role, sailor_repo, GUILD, context)
            for msg_str in award_msgs:
                await channel.send(msg_str)

        except Exception as e:
            log.error(f"Error in AutoCheckAwards: {e}", exc_info=True)
            await alert_engineers(
                self.bot,
                f"Error in AutoCheckAwards: {e}",
                exception=e
            )
            pass
        finally:
            sailor_repo.close_session()


    @my_task.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoCheckAwards(bot))