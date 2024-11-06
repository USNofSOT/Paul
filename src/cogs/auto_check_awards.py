import datetime
from logging import getLogger
from unittest.mock import MagicMock, AsyncMock

import discord
from discord.ext import commands, tasks
from discord.ext.commands.view import StringView

from src.config import MAX_MESSAGE_LENGTH
from src.config.main_server import GUILD_ID
from src.data.repository.sailor_repository import SailorRepository
from src.utils.check_awards import check_sailor
from src.utils.discord_utils import alert_engineers

log = getLogger(__name__)

# Super nasty: reconsider - Trigs
def fake_context(bot, channel_name="test-channel"):
    GUILD = bot.get_guild(GUILD_ID)

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

class AutoCheckAwards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    # TODO: Move this into configuration as well
    @tasks.loop(time=datetime.time(hour=14, minute=53, tzinfo=datetime.timezone.utc))
    async def my_task(self):
        GUILD = self.bot.get_guild(GUILD_ID)

        # TODO: Move this into configuration
        channels = {
            "USS Venom": {
                "channel": 1291589569602650154,
                "role": 1237838106711822457
            }
        }

        sailor_repo = SailorRepository()
        try:
            for i in channels:
                log.info(f"Checking awards for {i}")
                channel = GUILD.get_channel(channels[i]["channel"])
                role = GUILD.get_role(channels[i]["role"])
                members = role.members
                msg_str = ""
                for member in members:
                    # Check if member in database
                    sailor = sailor_repo.get_sailor(member.id)
                    if sailor is None:
                        continue

                    # Check for award messages for sailor
                    sailor_strs = check_sailor(self.bot, fake_context(self.bot, f"{i}"), sailor, member)
                    # Add strings to message, printing early if message would be too long
                    for sailor_str in sailor_strs:
                        if len(msg_str + sailor_str) <= MAX_MESSAGE_LENGTH:
                            msg_str += sailor_str
                        else:
                            await channel.send(msg_str)
                            msg_str = sailor_str
                if msg_str:
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