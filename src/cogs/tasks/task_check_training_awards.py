from logging import getLogger

from cogs.tasks.task_check_awards import fake_context
from config import GUILD_ID, NETC_ROLE, NRC_ROLE
from config.ranks import DECKHAND, RETIRED, VETERAN
from data import TrainingRecord
from data.repository.training_records_repository import TrainingRecordsRepository
from discord.ext import commands, tasks
from utils.check_awards import check_training

log = getLogger(__name__)

# Super nasty: reconsider - Trigs


class AutoCheckAwardsTraining(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    # TODO: Move this into configuration as well
    @tasks.loop(minutes=1)
    async def my_task(self):
        print("Checking awards")
        training_repository = TrainingRecordsRepository()
        channel = self.bot.get_guild(GUILD_ID).get_channel(1291589569602650154)

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

            sailor_strs = check_training(self.bot, fake_context(self.bot, ""), training_record, member)
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
            await channel.send(f"**Pending Training Awards for NRC Department**\n{nrc_str}")
        if netc_str:
            await channel.send(f"**Pending Training Awards for NETC Department**\n{netc_str}")


        training_repository.close_session()



    @my_task.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoCheckAwardsTraining(bot))
