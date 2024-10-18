import enum
import logging

from sqlalchemy.dialects.mysql import TINYTEXT
from sqlalchemy.sql.sqltypes import BOOLEAN, TEXT, DATETIME, Enum
from sqlalchemy import Column, Integer, BIGINT, ForeignKey, VARCHAR

from sqlalchemy.orm import declarative_base, mapped_column

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
    NETC = "NETC"
    JLA = "JLA"
    SNLA = "SNLA"
    OCS = "OCS"
    SOCS = "SOCS"

# Base class for all models
Base = declarative_base()

class AuditLogs(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    event = Column(TEXT)
    event_time = Column(DATETIME)


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

    def __str__(self):
        return f"[Sailor] {self.gamertag} ({self.discord_id})"

class Subclasses(Base):
    __tablename__ = "subclasses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = mapped_column(ForeignKey("sailor.discord_id"))
    log_id = Column(BIGINT)
    target_id = mapped_column(ForeignKey("sailor.discord_id"))
    subclass = Column(Enum(SubclassType))
    subclass_count = Column(Integer, server_default="1")
    log_time = Column(DATETIME)

class Voyages(Base):
    __tablename__ = "voyages"

    log_id = Column(BIGINT, primary_key=True)
    target_id = mapped_column(ForeignKey("sailor.discord_id"), primary_key=True)
    # amount = Column(Integer, server_default="1") Note: no longer needed
    log_time = Column(DATETIME)

class TrainingRecord(Base):
    __tablename__ = "training_records"

    target_id = mapped_column(BIGINT, ForeignKey("sailor.discord_id"), primary_key=True)
    nrc_training_points = Column(Integer, nullable=False, server_default="0")
    netc_training_points = Column(Integer, nullable=False, server_default="0")

    jla_training_points = Column(Integer, nullable=False, server_default="0")
    jla_graduation_date = Column(DATETIME, nullable=True, server_default=None)

    snla_training_points = Column(Integer, nullable=False, server_default="0")
    snla_graduation_date = Column(DATETIME, nullable=True, server_default=None)

    ocs_training_points = Column(Integer, nullable=False, server_default="0")
    ocs_graduation_date = Column(DATETIME, nullable=True, server_default=None)

    socs_training_points = Column(Integer, nullable=False, server_default="0")
    socs_graduation_date = Column(DATETIME, nullable=True, server_default=None)

class Training(Base):
    __tablename__ = "training"

    log_id = Column(BIGINT, primary_key=True, autoincrement=True)
    target_id = mapped_column(BIGINT, ForeignKey("sailor.discord_id"))
    log_channel_id = Column(BIGINT, nullable=False)
    training_type = Column(Enum(TraingType), nullable=False)
    training_category = Column(Enum(TrainingCategory), nullable=False)
    log_time = Column(DATETIME, nullable=False)

# Nifty function to create all tables
def create_tables():
    try:
        log.info("Attempting to create all tables")
        Base.metadata.create_all(engine)
    except Exception as e:
        log.error("Failed to create tables: %s", e)

if __name__ == '__main__':
    create_tables()
