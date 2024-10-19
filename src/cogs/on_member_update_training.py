"""
DEPRECATION NOTICE:
DO NOT USE THIS SNIPPET FOR TRAINING RECORDS MANAGEMENT

---

WE NO LONGER INTEND TO USE THIS BEHAVIOR FOR TRAINING RECORDS MANAGEMENT
"""

from logging import getLogger

from discord.ext import commands

from src.data.repository.training_records_repository import TrainingRecordsRepository

log = getLogger(__name__)


class OnMemberUpdateTraining(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        pass
        # if after.guild.id == NETC_GUILD_ID:
        #     training_repository = TrainingRecordsRepository()
        #     # Check which roles were added
        #     roles_added = [role for role in after.roles if role not in before.roles]
        #     roles_removed = [role for role in before.roles if role not in after.roles]
        #     if roles_added:
        #         log.info(f"[TRAINING] Roles added: {roles_added} to {after} in {after.guild.name}")
        #
        #     # Switch case for roles added
        #     for role in roles_added:
        #         if role.id == JLA_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] JLA Graduate role added to {after} in {after.guild.name}")
        #             training_repository.set_graduation(after.id, JLA_GRADUATE_ROLE)
        #             pass
        #         if role.id == SNLA_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] SNLA Graduate role added to {after} in {after.guild.name}")
        #             training_repository.set_graduation(after.id, SNLA_GRADUATE_ROLE)
        #             pass
        #         if role.id == OCS_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] OCS Graduate role added to {after} in {after.guild.name}")
        #             training_repository.set_graduation(after.id, OCS_GRADUATE_ROLE)
        #             pass
        #         if role.id == SOCS_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] SOCS Graduate role added to {after} in {after.guild.name}")
        #             training_repository.set_graduation(after.id, SOCS_GRADUATE_ROLE)
        #             pass
        #
        #     if roles_removed:
        #         log.info(f"[TRAINING] Roles removed: {roles_removed} from {after} in {after.guild.name}")
        #
        #     for role in roles_removed:
        #         if role.id == JLA_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] JLA Graduate role removed from {after} in {after.guild.name}")
        #             training_repository.remove_graduation(after.id, JLA_GRADUATE_ROLE)
        #             pass
        #         if role.id == SNLA_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] SNLA Graduate role removed from {after} in {after.guild.name}")
        #             training_repository.remove_graduation(after.id, SNLA_GRADUATE_ROLE)
        #             pass
        #         if role.id == OCS_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] OCS Graduate role removed from {after} in {after.guild.name}")
        #             training_repository.remove_graduation(after.id, OCS_GRADUATE_ROLE)
        #             pass
        #         if role.id == SOCS_GRADUATE_ROLE:
        #             log.info(f"[TRAINING] SOCS Graduate role removed from {after} in {after.guild.name}")
        #             training_repository.remove_graduation(after.id, SOCS_GRADUATE_ROLE)
        #             pass
        #
        #     training_repository.close_session()


async def setup(bot: commands.Bot):
    await bot.add_cog(OnMemberUpdateTraining(bot))