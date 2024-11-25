import enum
import logging
from typing import List

from sqlalchemy import Column, Integer, BIGINT, ForeignKey, VARCHAR
from sqlalchemy.dialects.mysql import TINYTEXT
from sqlalchemy.orm import declarative_base, mapped_column, relationship, Mapped
from sqlalchemy.sql.sqltypes import BOOLEAN, TEXT, DATETIME, Enum

from src.utils.time_utils import get_time_difference
from .engine import engine

log = logging.getLogger(__name__)

# Enumerated types for the different types of subclasses
class SubclassType(enum.Enum):
    CARPENTER = "Carpenter"
    FLEX = "Flex"
    CANNONEER = "Cannoneer"
    HELM = "Helm"
    GRENADIER = "Grenadier"
    SURGEON = "Surgeon"

class TrainingCategory(enum.Enum):
    NRC = "NRC"
    NETC = "NETC"

class TraingType(enum.Enum):
    NRC = "NRC"
    ST = "ST"
    NETC = "NETC"
    JLA = "JLA"
    SNLA = "SNLA"
    OCS = "OCS"
    SOCS = "SOCS"

# Base class for all models
Base = declarative_base()

class Coins(Base):
    __tablename__ = "coins"

    coin_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    coin_type = Column(TINYTEXT)
    moderator_id = mapped_column(ForeignKey("sailor.discord_id"))
    old_name = Column(TINYTEXT)
    coin_time = Column(DATETIME)


class ForceAdd(Base):
    __tablename__ = "force_add"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    add_type = Column(TINYTEXT)
    amount = Column(Integer)
    moderator_id = mapped_column(ForeignKey("sailor.discord_id"))
    add_time = Column(DATETIME)


class Hosted(Base):
    __tablename__ = "hosted"

    log_id = Column(BIGINT, primary_key=True)
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    # amount = Column(Integer, server_default="1") Note: no longer needed
    log_time = Column(DATETIME)
    ship_role_id = Column(BIGINT, nullable=True)

    # One-To-Many relationship with Voyages
    voyages: Mapped[List["Voyages"]] = relationship("Voyages", back_populates="hosted")
    # One-To-Many relationship with Subclasses
    subclasses: Mapped[List["Subclasses"]] = relationship("Subclasses", back_populates="hosted")
    # Many-to-One relationship with Sailor
    target: Mapped["Sailor"] = relationship("Sailor", foreign_keys=[target_id])


class ModNotes(Base):
    __tablename__ = "mod_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    moderator_id = mapped_column(ForeignKey("sailor.discord_id"))
    note = Column(TEXT)
    note_time = Column(DATETIME)
    hidden = Column(BOOLEAN, server_default="0")
    who_hid = mapped_column(ForeignKey("sailor.discord_id"))
    hide_time = Column(DATETIME)

class Subclasses(Base):
    __tablename__ = "subclasses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = mapped_column(ForeignKey("sailor.discord_id"))
    log_id = mapped_column(ForeignKey("hosted.log_id"))
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    subclass = Column(Enum(SubclassType))
    subclass_count = Column(Integer, server_default="1")
    log_time = Column(DATETIME)

    # Many-to-One relationship with Hosted
    hosted: Mapped["Hosted"] = relationship("Hosted", back_populates="subclasses", foreign_keys=[log_id])
    # Many-to-One relationship with Sailor for both the author and the target
    target: Mapped["Sailor"] = relationship("Sailor", foreign_keys=[target_id])
    author: Mapped["Sailor"] = relationship("Sailor", foreign_keys=[author_id])

class Voyages(Base):
    __tablename__ = "voyages"

    log_id = mapped_column(ForeignKey("hosted.log_id"), primary_key=True)
    target_id = mapped_column(ForeignKey("sailor.discord_id"), primary_key=True)
    # amount = Column(Integer, server_default="1") Note: no longer needed
    log_time = Column(DATETIME)
    ship_role_id = Column(BIGINT, nullable=True)

    # Many-to-One relationship with Hosted
    hosted: Mapped["Hosted"] = relationship("Hosted", back_populates="voyages", foreign_keys=[log_id])
    # Many-to-One relationship with Sailor
    target: Mapped["Sailor"] = relationship("Sailor", foreign_keys=[target_id])

class Sailor(Base):
    __tablename__ = "sailor"

    discord_id = mapped_column(BIGINT, primary_key=True)
    gamertag = Column(VARCHAR(32))
    timezone = Column(VARCHAR(32))
    award_ping_enabled = Column(BOOLEAN, server_default="1")
    carpenter_points = Column(Integer, server_default="0")
    flex_points = Column(Integer, server_default="0")
    cannoneer_points = Column(Integer, server_default="0")
    helm_points = Column(Integer, server_default="0")
    grenadier_points = Column(Integer, server_default="0")
    surgeon_points = Column(Integer, server_default="0")
    voyage_count = Column(Integer, server_default="0")
    hosted_count = Column(Integer, server_default="0")
    force_carpenter_points = Column(Integer, server_default="0")
    force_flex_points = Column(Integer, server_default="0")
    force_cannoneer_points = Column(Integer, server_default="0")
    force_helm_points = Column(Integer, server_default="0")
    force_grenadier_points = Column(Integer, server_default="0")
    force_surgeon_points = Column(Integer, server_default="0")
    force_voyage_count = Column(Integer, server_default="0")
    force_hosted_count = Column(Integer, server_default="0")

    # One-to-Many relationship with Hosted
    hosted: Mapped[List["Hosted"]] = relationship("Hosted", back_populates="target", foreign_keys=[Hosted.target_id])
    # One-to-Many relationship with Subclasses
    subclasses: Mapped[List["Subclasses"]] = relationship("Subclasses", back_populates="target", foreign_keys=[Subclasses.target_id])
    # One-to-Many relationship with Voyages
    voyages: Mapped[List["Voyages"]] = relationship("Voyages", back_populates="target", foreign_keys=[Voyages.target_id])

    def __str__(self):
        return f"[Sailor] {self.gamertag} ({self.discord_id})"


class TrainingRecord(Base):
    __tablename__ = "training_records"

    target_id = mapped_column(BIGINT, ForeignKey("sailor.discord_id"), primary_key=True)
    nrc_training_points = Column(Integer, nullable=False, server_default="0")
    netc_training_points = Column(Integer, nullable=False, server_default="0")

    st_training_points = Column(Integer, nullable=False, server_default="0")

    jla_training_points = Column(Integer, nullable=False, server_default="0")
    # jla_graduation_date = Column(DATETIME, nullable=True, server_default=None) - No longer being tracked

    snla_training_points = Column(Integer, nullable=False, server_default="0")
    # snla_graduation_date = Column(DATETIME, nullable=True, server_default=None) - No longer being tracked

    ocs_training_points = Column(Integer, nullable=False, server_default="0")
    # ocs_graduation_date = Column(DATETIME, nullable=True, server_default=None) - No longer being tracked

    socs_training_points = Column(Integer, nullable=False, server_default="0")
    # socs_graduation_date = Column(DATETIME, nullable=True, server_default=None) - No longer being tracked

    # Legacy training points (No longer being tracked)
    nla_training_points = Column(Integer, nullable=False, server_default="0")
    vla_training_points = Column(Integer, nullable=False, server_default="0")

class Training(Base):
    __tablename__ = "training"

    log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    target_id = mapped_column(BIGINT, ForeignKey("sailor.discord_id"))
    log_channel_id = Column(BIGINT, nullable=False)
    training_type = Column(Enum(TraingType), nullable=False)
    training_category = Column(Enum(TrainingCategory), nullable=False)
    log_time = Column(DATETIME, nullable=False)

""" AUDIT LOGS
The following classes are used for audit logging 

Things we may log are
- Name changes
- Role Changes
- Moderation actions
- Commands used?

We may refer to the Sailor class for the discord_id as 
- target_id (the person who the action was taken on)
- changed_by (the person who took the action)
"""

class AuditLogBare(Base):
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True) # The internal identifier

    target_id = mapped_column(ForeignKey("sailor.discord_id"), nullable=False) # The person who the action was taken on
    guild_id = Column(BIGINT, nullable=False) # The guild the action was taken in

    log_time = Column(DATETIME, nullable=False)


class AuditLog(AuditLogBare):
    __abstract__ = True
    changed_by_id = mapped_column(ForeignKey("sailor.discord_id")) # The person who took the action

class BanChangeLog(AuditLog):
    __tablename__ = "log_ban_change"
    reason = Column(TEXT, nullable=True)

class LeaveChangeLog(AuditLogBare):
    __tablename__ = "log_leave_change"
    e2_or_above = Column(BOOLEAN, server_default="0")
    ship_role_id = Column(BIGINT, nullable=True)

class NameChangeLog(AuditLog):
    __tablename__ = "log_name_change"

    name_before = Column(VARCHAR(32))
    name_after = Column(VARCHAR(32))

class RoleChangeType(enum.Enum):
    ADDED = "Add"
    REMOVED = "Remove"

class RoleChangeLog(AuditLog):
    __tablename__ = "log_role_change"

    change_type = Column(Enum(RoleChangeType), nullable=False) # Whether the role was added or removed
    role_id = Column(BIGINT, nullable=False) # The role that was added or removed
    role_name = Column(VARCHAR(32), nullable=False) # The name of the role

class TimeoutLog(AuditLog):
    __tablename__ = "log_timeout"

    # The timeout time before the new timeout was applied
    timed_out_until_before = Column(DATETIME, nullable=True)
    # The timeout time after the new timeout was applied (current timeout)
    timed_out_until = Column(DATETIME, nullable=True)

    @property
    def timeout_removed(self) -> bool:
        """Returns True if this timeout log was for a removal of a timeout."""
        return self.timed_out_until is None

    @property
    def timeout_added(self) -> bool:
        """Returns True if this timeout log was for an addition of a timeout."""
        return self.timed_out_until_before is None

    @property
    def length(self) -> float:
        """Calculates the length of the timeout. Given log_time is the time the timeout was applied."""
        if self.timeout_removed:
            return 0
        return get_time_difference(self.timed_out_until, self.log_time)

class BotInteractionType(enum.Enum):
    INTERACTION = "Interaction"
    COMMAND = "Command"

class BotInteractionLog(AuditLogBare):
    __tablename__ = "log_bot_interaction"

    interaction_type = Column(Enum(BotInteractionType), nullable=False)
    channel_id = Column(BIGINT, nullable=True)
    command_name = Column(VARCHAR(32), nullable=True)
    failed = Column(BOOLEAN, server_default="0")

    @property
    def timeout_removed(self) -> bool:
        """Returns True if this timeout log was for a removal of a timeout."""
        return self.timed_out_until is None

    @property
    def timeout_added(self) -> bool:
        """Returns True if this timeout log was for an addition of a timeout."""
        return self.timed_out_until_before is None

    @property
    def length(self) -> float:
        """Calculates the length of the timeout. Given log_time is the time the timeout was applied."""
        if self.timeout_removed:
            return 0
        return get_time_difference(self.timed_out_until, self.log_time)

# Nifty function to create all tables
def create_tables():
    try:
        log.info("Attempting to create all tables")
        Base.metadata.create_all(engine)
    except Exception as e:
        log.error("Failed to create tables: %s", e)

if __name__ == '__main__':
    create_tables()
