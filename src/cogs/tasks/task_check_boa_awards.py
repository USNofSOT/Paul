from logging import getLogger

from discord.ext import commands, tasks

from src.config import BOA_ROLE
from src.config.main_server import BC_BOA, GUILD_ID
from src.config.task_timing import CHECK_BOA_AWARDS_TASK_TIME
from src.data.repository.sailor_repository import SailorRepository
from src.utils.award_messages import create_award_messages, fake_context

log = getLogger(__name__)


class CheckBoaAwardsTask(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.check_boa_awards.start()

    def cog_unload(self) -> None:
        self.check_boa_awards.cancel()

    @tasks.loop(time=CHECK_BOA_AWARDS_TASK_TIME)
    async def check_boa_awards(self) -> None:
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            log.warning("BOA awards skipped because the guild is unavailable.")
            return
        boa_role = guild.get_role(BOA_ROLE)
        channel = guild.get_channel(BC_BOA)
        if boa_role is None or channel is None:
            log.warning(
                "BOA awards skipped because its role or channel is unavailable.",
            )
            return

        sailor_repository = SailorRepository()
        try:
            context = fake_context(self.bot, guild, "Board of Admiralty")
            messages = create_award_messages(
                boa_role,
                sailor_repository,
                guild,
                context,
            )
            for message in messages:
                await channel.send(message)
        except Exception:
            log.exception(
                "Error checking BOA awards.",
                extra={"notify_engineer": True},
            )
        finally:
            sailor_repository.close_session()

    @check_boa_awards.before_loop
    async def before_check_boa_awards(self) -> None:
        await self.bot.wait_until_ready()

    @check_boa_awards.error
    async def check_boa_awards_error(self, error: Exception) -> None:
        log.error(
            "BOA awards task stopped unexpectedly.",
            exc_info=error,
            extra={"notify_engineer": True},
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CheckBoaAwardsTask(bot))
