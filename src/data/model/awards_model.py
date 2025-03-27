import enum
import logging
from typing import List

import discord
from data import Base
from data.model.award_recipients_model import AwardRecipients
from sqlalchemy import Boolean, Column, Enum, Integer
from sqlalchemy.dialects.mysql import BIGINT, DATETIME, VARCHAR
from sqlalchemy.orm import Mapped, relationship
from utils.rank_and_promotion_utils import has_award_or_higher

from src.config import GUILD_ID

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
        Enum(AwardCategory), nullable=True, server_default="MISCELLANEOUS"
    )

    # Threshold value for the award, and the ranks responsible for the award
    threshold = Column(Integer, nullable=True)
    ranks_responsible = Column(VARCHAR(64), nullable=True)

    # Identifiers for the role, channel thread, and embed if applicable
    role_id = Column(BIGINT, nullable=True)
    channel_thread_id = Column(BIGINT, nullable=True)
    embed_id = Column(BIGINT, nullable=True)

    # Whether the award is a streak award
    is_streak = Column(Boolean)
    is_tiered = Column(Boolean, server_default="0")

    # Flags for showing and hiding the award
    is_hidden = Column(Boolean, server_default="0")
    only_show_for_recipient = Column(Boolean, server_default="0")

    # Created, edited, and deleted timestamps
    created_at = Column(DATETIME, nullable=True)
    edited_at = Column(DATETIME, nullable=True)

    # Relationships
    recipients: Mapped[List["AwardRecipients"]] = relationship(
        "AwardRecipients",
        back_populates="award",
    )

    @property
    def is_role_award(self) -> bool:
        return self.role_id is not None

    @property
    def embed_url(self) -> str or None:
        """
        Return the URL for the embed if it exists, otherwise return None
        """
        if self.channel_thread_id == 0 or self.embed_id == 0:
            return None
        return f"https://discord.com/channels/{GUILD_ID}/{self.channel_thread_id}/{self.embed_id}"

    def has_award(self, member: discord.Member, category_awards=None) -> bool:
        """
        Check if the member has the award.

        Args:
            member:  The discord.Member object to check for the award
            category_awards:  The list of awards in the category to check for higher awards

        Returns: True if the member has the award, False otherwise
        """
        try:
            has_award = any(
                recipient.target_id == member.id for recipient in self.recipients
            )
            if self.is_role_award:
                has_award = self.role_id in [role.id for role in member.roles]
                if category_awards:
                    has_award = has_award_or_higher(member, self, category_awards)
        except Exception as e:
            log.exception("Error checking if member has award: %s", e)
            return False
        return has_award
