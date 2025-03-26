import enum
import logging

import discord
from data import Base
from sqlalchemy import Boolean, Column, Enum, Integer
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR
from utils.rank_and_promotion_utils import has_award_or_higher

log = logging.getLogger(__name__)


class AwardCategory(enum.Enum):
    VOYAGE = "Voyage"
    HOSTED = "Hosted"
    COMBAT = "Combat"
    TRAINING = "Training"
    CONDUCT = "Conduct"
    RECRUIT = "Recruit"
    ATTENDANCE = "Attendance"
    SERVICE = "Service"
    MISCELLANEOUS = "Miscellaneous"


class Awards(Base):
    __tablename__ = "awards"

    # Primary key for the awards table
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Contextual information about the award
    name = Column(VARCHAR(64), nullable=False)
    description = Column(VARCHAR(255), nullable=True)
    category = Column(
        Enum(AwardCategory), nullable=True, default=AwardCategory.MISCELLANEOUS
    )

    # Threshold value for the award, and the ranks responsible for the award
    threshold = Column(Integer, nullable=True)
    ranks_responsible = Column(VARCHAR(64), nullable=True)

    # Identifiers for the role, channel thread, and embed if applicable
    role_id = Column(BIGINT, nullable=True)
    channel_thread_id = Column(BIGINT, nullable=True)
    embed_id = Column(BIGINT, nullable=True)

    # Whether the award is a streak award
    is_streak = Column(Boolean, default=False)
    # Whether the award is a tiered award
    is_tiered = Column(Boolean, default=False, nullable=False)

    # Created, edited, and deleted timestamps
    created_at = Column(DATETIME, nullable=True)
    edited_at = Column(DATETIME, nullable=True)

    @property
    def is_role_award(self) -> bool:
        return self.role_id is not None

    @property
    def embed_url(self) -> str:
        if self.channel_thread_id == 0 or self.embed_id == 0:
            return None
        return f"https://discord.com/channels/{933907909954371654}/{self.channel_thread_id}/{self.embed_id}"

    def has_award(self, member: discord.Member, category_awards=None) -> bool:
        """
        Check if the member has the award.

        Args:
            member:  The discord.Member object to check for the award
            category_awards:  The list of awards in the category to check for higher awards

        Returns: True if the member has the award, False otherwise
        """
        has_award = False
        try:
            if self.is_role_award:
                has_award = self.role_id in [role.id for role in member.roles]
                if self.is_role_award and category_awards:
                    has_award = has_award_or_higher(member, self, category_awards)
            else:
                # TODO: Implement database check
                return False
        except Exception as e:
            log.exception("Error checking if member has award: %s", e)
            return False
        return has_award
