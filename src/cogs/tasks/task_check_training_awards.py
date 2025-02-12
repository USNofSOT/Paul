import datetime
from logging import getLogger

from cogs.tasks.task_check_awards import fake_context
from config import (
    CO_OF_NETC_ROLE,
    GUILD_ID,
    NETC_BOT_CHANNEL,
    NETC_GUILD_ID,
    NETC_ROLE,
    NRC_ROLE,
)
from config.ranks import DECKHAND, RETIRED, VETERAN
from data import TrainingRecord
from data.repository.training_records_repository import TrainingRecordsRepository
from discord.ext import commands, tasks
from utils.check_awards import check_training
from utils.discord_utils import alert_engineers

log = getLogger(__name__)

# Super nasty: reconsider - Trigs


class AutoCheckAwardsTraining(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    # TODO: Move this into configuration as well
    @tasks.loop(time=datetime.time(hour=15, minute=00, tzinfo=datetime.timezone.utc))
    async def my_task(self):
        log.info("Checking training awards")
        training_repository = TrainingRecordsRepository()

        try:
            nrc_channel = self.bot.get_guild(GUILD_ID).get_channel(1291589569602650154)
            netc_channel = self.bot.get_guild(NETC_GUILD_ID).get_channel(NETC_BOT_CHANNEL)

            # Get all training records
            training_records = training_repository.get_session().query(TrainingRecord).all()

            # Filter out records based on conditions
            guild = self.bot.get_guild(GUILD_ID)
            training_records = [
                record for record in training_records
                if guild.get_member(record.target_id) is not None and
                   DECKHAND.role_ids[0] not in [role.id for role in guild.get_member(record.target_id).roles] and
                   VETERAN.role_ids[0] not in [role.id for role in guild.get_member(record.target_id).roles] and
                   RETIRED.role_ids[0] not in [role.id for role in guild.get_member(record.target_id).roles]
            ]

            nrc_str = ""
            netc_str = ""

            for training_record in training_records:
                member = self.bot.get_guild(GUILD_ID).get_member(training_record.target_id)

                in_nrc = member is not None and NRC_ROLE in [role.id for role in member.roles]
                in_netc = member is not None and NETC_ROLE in [role.id for role in member.roles]

                sailor_strs = check_training(guild, fake_context(self.bot, ""), training_record, member)
                if sailor_strs:
                    # If person is part of NRC Department and not NETC Department dedicates to NRC
                    if in_nrc and not in_netc:
                        nrc_str += f"{''.join(sailor_strs)}"
                    # If person is part of NETC Department and not NRC Department dedicates to NETC
                    elif in_netc and not in_nrc:
                        netc_str += f"{''.join(sailor_strs)}"
                    # If the person is part of both departments or neither, go by majority of points
                    else:
                        nrc_points = training_record.nrc_training_points + training_record.st_training_points
                        netc_points = training_record.netc_training_points
                        if nrc_points > netc_points:
                            nrc_str += f"{''.join(sailor_strs)}"
                        elif netc_points > nrc_points:
                            netc_str += f"{''.join(sailor_strs)}"
                        # If points are equal, pick randomly
                        else:
                            if member.id % 2 == 0:
                                nrc_str += f"{''.join(sailor_strs)}"
                            else:
                                netc_str += f"{''.join(sailor_strs)}"

            if nrc_str:
                log.info(f"Send NRC Training Awards to channel #{nrc_channel.name} in {nrc_channel.guild.name}")
                await nrc_channel.send(f"**Pending Training Awards for NRC Department**\n{nrc_str}")
            if netc_str:
                log.info(f"Send NETC Training Awards to channel #{netc_channel.name} in {netc_channel.guild.name}")
                await netc_channel.send(f"**Pending Training Awards for NETC Department (<@&{CO_OF_NETC_ROLE}>)**\n{netc_str}")

        except Exception as e:
            log.error(f"Error in AutoCheckAwards: {e}", exc_info=True)
            await alert_engineers(
                self.bot,
                f"Error in AutoCheckAwards: {e}",
                exception=e
            )
        finally:
            training_repository.close_session()



    @my_task.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoCheckAwardsTraining(bot))
