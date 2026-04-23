import enum
import logging

from sqlalchemy import (
    BIGINT,
    FLOAT,
    VARCHAR,
    Column,
    Date,
    ForeignKey,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.mysql import TINYTEXT
from sqlalchemy.orm import Mapped, declarative_base, mapped_column, relationship
from sqlalchemy.sql.sqltypes import BOOLEAN, DATETIME, TEXT, Enum

from src.utils.time_utils import get_time_difference, utc_time_now
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
    SLA = "SLA"
    COSA = "COSA"
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


class VoyageType(enum.Enum):
    UNKNOWN = "Unknown"
    SKIRMISH = "Skirmish"
    PATROL = "Patrol"
    ADVENTURE = "Adventure"
    CONVOY = "Convoy"


class Hosted(Base):
    __tablename__ = "hosted"

    log_id = Column(BIGINT, primary_key=True)
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    # amount = Column(Integer, server_default="1") Note: no longer needed
    log_time = Column(DATETIME)
    ship_role_id = Column(BIGINT, nullable=True)

    voyage_type = Column(
        Enum(VoyageType), server_default="Unknown", nullable=False
    )  # The type of voyage

    gold_count = Column(
        Integer, server_default="0", nullable=True
    )  # The number of gold given in the log
    doubloon_count = Column(
        Integer, server_default="0", nullable=True
    )  # The number of doubloons given in the log
    ancient_coin_count = Column(
        Integer, server_default="0", nullable=True
    )  # The number of ancient coins given in the log
    fish_count = Column(
        Integer, server_default="0", nullable=True
    )  # The number of fish given in the log

    ship_voyage_count = Column(
        Integer, server_default="0", nullable=True
    )  # The voyage number for the ship for this log

    ship_name = Column(VARCHAR(32), nullable=True)  # e.g. "USS Venom"
    auxiliary_ship_name = Column(
        VARCHAR(32), nullable=True
    )  # e.g. "USS Auxiliary" which would be the auxiliary ship for the USS Venom

    # One-To-Many relationship with Voyages
    voyages: Mapped[list["Voyages"]] = relationship("Voyages", back_populates="hosted")
    # One-To-Many relationship with Subclasses
    subclasses: Mapped[list["Subclasses"]] = relationship(
        "Subclasses", back_populates="hosted"
    )
    # Many-to-One relationship with Sailor
    target: Mapped["Sailor"] = relationship("Sailor", foreign_keys=[target_id])

    voyage_planning_channel_id = Column(BIGINT,
                                        nullable=True)  # The channel ID of the voyage planning or announcement message (if any)
    voyage_planning_message_id = Column(BIGINT,
                                        nullable=True)  # The message ID of the voyage planning or announcement message (if any)


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
    hosted: Mapped["Hosted"] = relationship(
        "Hosted", back_populates="subclasses", foreign_keys=[log_id]
    )
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
    hosted: Mapped["Hosted"] = relationship(
        "Hosted", back_populates="voyages", foreign_keys=[log_id]
    )
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
    last_voyage_at = Column(DATETIME, nullable=True)
    last_hosting_at = Column(DATETIME, nullable=True)

    # One-to-Many relationship with Hosted
    hosted: Mapped[list["Hosted"]] = relationship(
        "Hosted", back_populates="target", foreign_keys=[Hosted.target_id]
    )
    # One-to-Many relationship with Subclasses
    subclasses: Mapped[list["Subclasses"]] = relationship(
        "Subclasses", back_populates="target", foreign_keys=[Subclasses.target_id]
    )
    # One-to-Many relationship with Voyages
    voyages: Mapped[list["Voyages"]] = relationship(
        "Voyages", back_populates="target", foreign_keys=[Voyages.target_id]
    )

    def __str__(self):
        return f"[Sailor] {self.gamertag} ({self.discord_id})"


class ShipSize(Base):
    __tablename__ = "ship_size"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ship_role_id = Column(BIGINT, primary_key=True)
    member_count = Column(Integer, nullable=False)
    log_time = Column(DATETIME, nullable=False, index=True)


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

    sla_training_points = Column(Integer, nullable=False, server_default="0")
    cosa_training_points = Column(Integer, nullable=False, server_default="0")

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
    log_time = Column(DATETIME, nullable=False, index=True)


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

    id = Column(
        Integer, primary_key=True, autoincrement=True
    )  # The internal identifier

    target_id = mapped_column(
        ForeignKey("sailor.discord_id"), nullable=False
    )  # The person who the action was taken on
    guild_id = Column(BIGINT, nullable=False)  # The guild the action was taken in

    log_time = Column(DATETIME, nullable=False, index=True)


class AuditLog(AuditLogBare):
    __abstract__ = True
    changed_by_id = mapped_column(
        ForeignKey("sailor.discord_id")
    )  # The person who took the action


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

    change_type = Column(
        Enum(RoleChangeType), nullable=False
    )  # Whether the role was added or removed
    role_id = Column(BIGINT, nullable=False)  # The role that was added or removed
    role_name = Column(VARCHAR(32), nullable=False)  # The name of the role


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
    interaction_id = Column(BIGINT, nullable=True, index=True)
    execution_time_ms = Column(FLOAT, nullable=True)
    args = Column(TEXT, nullable=True)
    error_message = Column(TEXT, nullable=True)

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


class HealthSnapshot(Base):
    __tablename__ = "health_snapshot"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DATETIME, nullable=False, index=True)
    pool_size = Column(Integer, nullable=False)
    checked_out = Column(Integer, nullable=False)
    overflow = Column(Integer, nullable=False)
    checked_in = Column(Integer, nullable=False)
    avg_cmd_latency = Column(FLOAT, nullable=True)
    max_cmd_latency = Column(FLOAT, nullable=True)
    memory_usage_mb = Column(FLOAT, nullable=False)
    discord_latency_ms = Column(FLOAT, nullable=True)
    bot_cpu_usage_percent = Column(FLOAT, nullable=True)
    system_cpu_usage_percent = Column(FLOAT, nullable=True)
    system_total_memory_mb = Column(FLOAT, nullable=True)
    user_count = Column(Integer, nullable=True)


class SecurityEventType(enum.Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class UserRole(Base):
    __tablename__ = "user_roles"

    discord_id = mapped_column(BIGINT, ForeignKey("sailor.discord_id"), primary_key=True)
    role_name = Column(VARCHAR(64), primary_key=True)


class SecurityInteractionAuditLog(Base):
    __tablename__ = "security_interaction_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    discord_id = Column(BIGINT, nullable=False)
    command_name = Column(VARCHAR(128), nullable=False)
    event_type = Column(Enum(SecurityEventType), nullable=False)
    details = Column(TEXT, nullable=True)
    args = Column(TEXT, nullable=True)
    created_at = Column(DATETIME, nullable=False, default=utc_time_now)


class CacheStat(Base):
    __tablename__ = "cache_stats"

    cache_name = Column(VARCHAR(64), primary_key=True)
    request_count = Column(Integer, nullable=False, server_default="0")
    cache_hit_count = Column(Integer, nullable=False, server_default="0")
    cache_miss_count = Column(Integer, nullable=False, server_default="0")
    cached_percent = Column(FLOAT, nullable=False, server_default="0")
    last_requested_at = Column(DATETIME, nullable=True)
    last_cache_hit_at = Column(DATETIME, nullable=True)
    last_cache_miss_at = Column(DATETIME, nullable=True)
    janitor_run_count = Column(Integer, nullable=False, server_default="0")
    janitor_removed_expired_count = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
    janitor_removed_overflow_count = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
    janitor_last_removed_expired = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
    janitor_last_removed_overflow = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
    janitor_last_remaining_items = Column(
        Integer,
        nullable=False,
        server_default="0",
    )
    janitor_last_run_at = Column(DATETIME, nullable=True)


class CommandCooldownStat(Base):
    __tablename__ = "command_cooldown_stats"

    command_name = Column(VARCHAR(64), primary_key=True)
    cooldown_seconds = Column(Integer, nullable=False, server_default="0")
    trigger_count = Column(Integer, nullable=False, server_default="0")
    last_triggered_at = Column(DATETIME, nullable=True)
    last_retry_after_seconds = Column(
        Integer,
        nullable=False,
        server_default="0",
    )


class NotificationEvent(Base):
    __tablename__ = "notification_events"
    __table_args__ = (
        UniqueConstraint(
            "notification_type",
            "sailor_id",
            "threshold_at",
            "trigger_offset",
            name="uq_notification_events_deduplication",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    notification_type = Column(VARCHAR(64), nullable=False)
    status = Column(VARCHAR(32), nullable=False)
    sailor_id = mapped_column(ForeignKey("sailor.discord_id"), nullable=False)
    ship_role_id = Column(BIGINT, nullable=True)
    squad_role_id = Column(BIGINT, nullable=True)
    source_activity_at = Column(DATETIME, nullable=True)
    source_activity_date = Column(Date, nullable=False)
    threshold_at = Column(DATETIME, nullable=False)
    threshold_date = Column(Date, nullable=False)
    trigger_offset = Column(Integer, nullable=False)
    scheduled_for_at = Column(DATETIME, nullable=False)
    scheduled_for_date = Column(Date, nullable=False)
    destination_channel_id = Column(BIGINT, nullable=True)
    payload_snapshot = Column(TEXT, nullable=True)
    skip_reason = Column(TEXT, nullable=True)
    failure_reason = Column(TEXT, nullable=True)
    attempt_count = Column(Integer, nullable=False, server_default="0")
    claimed_at = Column(DATETIME, nullable=True)
    delivered_at = Column(DATETIME, nullable=True)
    created_at = Column(DATETIME, nullable=False)
    updated_at = Column(DATETIME, nullable=False)


# Nifty function to create all tables
def create_tables():
    try:
        log.info("Attempting to create all tables")
        Base.metadata.create_all(engine)
    except Exception as e:
        log.error("Failed to create tables: %s", e)


if __name__ == "__main__":
    create_tables()
