import logging

from data import Base, Sailor
from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.orm import Mapped, mapped_column, relationship

log = logging.getLogger(__name__)


class AwardRecipients(Base):
    __tablename__ = "award_recipients"
    __table_args__ = (
        UniqueConstraint("target_id", "award_id", name="_target_award_uc"),
    )

    # Primary key for the awards table
    id = Column(Integer, primary_key=True, autoincrement=True)

    # FK to the sailor receiving the award
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    # FK to the sailor giving the award
    moderator_id = mapped_column(ForeignKey("sailor.discord_id"))
    # FK to the award being received
    award_id = mapped_column(ForeignKey("awards.id"))

    # Relationships
    target: Mapped["Sailor"] = relationship("Sailor", foreign_keys=[target_id])
    moderator: Mapped["Sailor"] = relationship("Sailor", foreign_keys=[moderator_id])
    award: Mapped["Awards"] = relationship(  # noqa: F821
        "Awards", foreign_keys=[award_id]
    )

    # Created, edited, and deleted timestamps
    created_at = Column(DATETIME, nullable=False)
