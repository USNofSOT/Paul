from logging import getLogger

from discord.ext import commands, tasks

from config import (
    CO_OF_NETC_ROLE,
    CO_OF_NRC_ROLE,
    GUILD_ID,
    NETC_BOT_CHANNEL,
    NETC_GUILD_ID,
    NETC_ROLE,
    NRC_CMD_CHANNEL,
    NRC_ROLE,
    SPD_GUILD_ID,
    XO_OF_NETC_ROLE,
)
from config.ranks import DECKHAND, RETIRED, VETERAN
from data import TrainingRecord
from data.repository.training_records_repository import TrainingRecordsRepository
from src.config.task_timing import CHECK_TRAINING_AWARDS_TASK_TIME
from src.utils.award_messages import fake_context
from utils.check_awards import check_training

log = getLogger(__name__)

# Super nasty: reconsider - Trigs


class AutoCheckAwardsTraining(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    @tasks.loop(time=CHECK_TRAINING_AWARDS_TASK_TIME)
    async def my_task(self):
        log.info("Checking training awards")
        training_repository = TrainingRecordsRepository()

        try:
            nrc_guild = self.bot.get_guild(SPD_GUILD_ID)
            netc_guild = self.bot.get_guild(NETC_GUILD_ID)
            guild = self.bot.get_guild(GUILD_ID)
            if nrc_guild is None or netc_guild is None or guild is None:
                log.warning(
                    "Training awards skipped because a required guild is unavailable.",
                )
                return

            nrc_channel = nrc_guild.get_channel(NRC_CMD_CHANNEL)
            netc_channel = netc_guild.get_channel(NETC_BOT_CHANNEL)
            if nrc_channel is None or netc_channel is None:
                log.warning(
                    "Training awards skipped because a configured channel is "
                    "unavailable.",
                )
                return

            # Get all training records
            training_records = (
                training_repository.get_session().query(TrainingRecord).all()
            )

            # Filter out records based on conditions
            training_records = [
                record
                for record in training_records
                if guild.get_member(record.target_id) is not None
                and DECKHAND.role_ids[0]
                not in [role.id for role in guild.get_member(record.target_id).roles]
                and VETERAN.role_ids[0]
                not in [role.id for role in guild.get_member(record.target_id).roles]
                and RETIRED.role_ids[0]
                not in [role.id for role in guild.get_member(record.target_id).roles]
            ]

            nrc_str = ""
            netc_str = ""

            for training_record in training_records:
                member = self.bot.get_guild(GUILD_ID).get_member(
                    training_record.target_id
                )

                in_nrc = member is not None and NRC_ROLE in [
                    role.id for role in member.roles
                ]
                in_netc = member is not None and NETC_ROLE in [
                    role.id for role in member.roles
                ]

                sailor_strs = check_training(
                    guild, fake_context(self.bot, ""), training_record, member
                )
                if sailor_strs:
                    # Members in only one department belong to that department.
                    if in_nrc and not in_netc:
                        nrc_str += f"{''.join(sailor_strs)}"
                    elif in_netc and not in_nrc:
                        netc_str += f"{''.join(sailor_strs)}"
                    # Otherwise, use the department where they earned most.
                    else:
                        nrc_points = (
                            training_record.nrc_training_points
                            + training_record.st_training_points
                        )
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
                log.info(
                    "Send NRC Training Awards to channel #%s in %s",
                    nrc_channel.name,
                    nrc_channel.guild.name,
                )
                await nrc_channel.send(
                    "**Pending Training Awards for NRC Department "
                    f"(<@&{CO_OF_NRC_ROLE}>)**\n{nrc_str}"
                )
            if netc_str:
                log.info(
                    "Send NETC Training Awards to channel #%s in %s",
                    netc_channel.name,
                    netc_channel.guild.name,
                )
                await netc_channel.send(
                    "**Pending Training Awards for NETC Department "
                    f"(<@&{CO_OF_NETC_ROLE}> <@&{XO_OF_NETC_ROLE}>)**\n"
                    f"{netc_str}"
                )

        except Exception as e:
            log.error(
                f"Error in AutoCheckTrainingAwards: {e}",
                exc_info=True,
                extra={"notify_engineer": True},
            )
        finally:
            training_repository.close_session()

    @my_task.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()

    @my_task.error
    async def my_task_error(self, error: Exception) -> None:
        log.error(
            "Training awards task stopped unexpectedly.",
            exc_info=error,
            extra={"notify_engineer": True},
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoCheckAwardsTraining(bot))
