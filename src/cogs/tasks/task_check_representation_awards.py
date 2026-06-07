from logging import getLogger

from discord.ext import commands, tasks

from src.cogs.tasks.task_check_awards import append_award_message_chunk, fake_context
from src.config import MAX_MESSAGE_LENGTH
from src.config.main_server import GUILD_ID
from src.config.ranks import DECKHAND, RETIRED, VETERAN
from src.config.representation import (
    HEAD_OF_MEDIA_ROLE_ID,
    HEAD_OF_SCHEDULING_ROLE_ID,
    MEDIA_REPRESENTATION_AWARDS_CHANNEL,
    XO_OF_MEDIA_ROLE_ID,
    XO_OF_SCHEDULING_ROLE_ID,
    SCHEDULING_REPRESENTATION_AWARDS_CHANNEL,
)
from src.config.task_timing import CHECK_REPRESENTATION_AWARDS_TASK_TIME
from src.data.models import RepresentationDepartment, RepresentationPoints
from src.data.repository.representation_repository import RepresentationRepository
from src.utils.check_awards import check_representation
from src.utils.representation_utils import choose_representation_department

log = getLogger(__name__)


def _member_is_excluded(member_role_ids: set[int]) -> bool:
    return (
            DECKHAND.role_ids[0] in member_role_ids
            or VETERAN.role_ids[0] in member_role_ids
            or RETIRED.role_ids[0] in member_role_ids
    )


def _build_pending_representation_header(
        department: RepresentationDepartment,
) -> str:
    if department == RepresentationDepartment.MEDIA:
        return (
            f"**Pending Representation Awards for Media Department "
            f"(<@&{HEAD_OF_MEDIA_ROLE_ID}> <@&{XO_OF_MEDIA_ROLE_ID}>)**\n"
        )
    return (
        f"**Pending Representation Awards for Scheduling Department "
        f"(<@&{HEAD_OF_SCHEDULING_ROLE_ID}> <@&{XO_OF_SCHEDULING_ROLE_ID}>)**\n"
    )


def _build_pending_representation_messages(
        department: RepresentationDepartment,
        award_messages: list[str],
        max_message_length: int = MAX_MESSAGE_LENGTH,
) -> list[str]:
    header = _build_pending_representation_header(department)
    body_max_length = max_message_length - len(header)
    pending_messages: list[str] = []
    current_body = ""

    for award_message in award_messages:
        current_body = append_award_message_chunk(
            pending_messages,
            current_body,
            award_message,
            body_max_length,
        )

    if current_body:
        pending_messages.append(current_body)

    return [header + message for message in pending_messages]


class AutoCheckRepresentationAwards(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    @tasks.loop(time=CHECK_REPRESENTATION_AWARDS_TASK_TIME)
    async def my_task(self):
        log.info("Checking representation awards")
        representation_repository = RepresentationRepository()

        try:
            guild = self.bot.get_guild(GUILD_ID)
            if guild is None:
                log.warning("Representation awards task skipped because main guild was not found.")
                return

            media_channel = self.bot.get_channel(MEDIA_REPRESENTATION_AWARDS_CHANNEL)
            scheduling_channel = self.bot.get_channel(SCHEDULING_REPRESENTATION_AWARDS_CHANNEL)

            representation_records = (
                representation_repository.get_session().query(RepresentationPoints).all()
            )

            media_messages: list[str] = []
            scheduling_messages: list[str] = []

            for representation_record in representation_records:
                member = guild.get_member(representation_record.target_id)
                if member is None:
                    continue

                member_role_ids = {role.id for role in member.roles}
                if _member_is_excluded(member_role_ids):
                    continue

                sailor_str = check_representation(
                    guild,
                    fake_context(self.bot, guild, "representation-awards"),
                    representation_record,
                    member,
                )
                if not sailor_str:
                    continue

                department = choose_representation_department(
                    media_points=representation_record.media_representation_points,
                    scheduling_points=representation_record.scheduling_representation_points,
                )
                if department == RepresentationDepartment.MEDIA:
                    media_messages.append(sailor_str)
                else:
                    scheduling_messages.append(sailor_str)

            if media_messages and media_channel is not None:
                log.info("Sending pending representation awards to media channel.")
                for message in _build_pending_representation_messages(
                        RepresentationDepartment.MEDIA,
                        media_messages,
                ):
                    await media_channel.send(message)

            if scheduling_messages and scheduling_channel is not None:
                log.info("Sending pending representation awards to scheduling channel.")
                for message in _build_pending_representation_messages(
                        RepresentationDepartment.SCHEDULING,
                        scheduling_messages,
                ):
                    await scheduling_channel.send(message)

        except Exception as e:
            log.error(
                "Error in AutoCheckRepresentationAwards: %s",
                e,
                exc_info=True,
                extra={"notify_engineer": True},
            )
        finally:
            representation_repository.close_session()

    @my_task.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoCheckRepresentationAwards(bot))
