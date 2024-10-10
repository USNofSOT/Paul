import logging

from sqlalchemy.dialects.mysql import TINYTEXT
from sqlalchemy.sql.sqltypes import BOOLEAN, TEXT, DATETIME
from sqlalchemy import Column, Integer, BIGINT, ForeignKey

from sqlalchemy.orm import declarative_base, Mapped, mapped_column

from engine import engine

log = logging.getLogger(__name__)
Base = declarative_base()


class AuditLogs(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    event = Column(TEXT)
    event_time = Column(DATETIME)


class Coins(Base):
    __tablename__ = "coins"

    coin_id = Column(Integer, primary_key=True, nullable=False, autoincrement=True)
    target_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    coin_nam = Column(TEXT)
    coin_type = Column(TINYTEXT)
    moderator_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    old_name = Column(TINYTEXT)
    coin_time = Column(DATETIME)


class ForceAdd(Base):
    __tablename__ = "force_add"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    add_type = Column(TINYTEXT)
    amount = Column(Integer)
    moderator_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    add_time = Column(DATETIME)


class Hosted(Base):
    __tablename__ = "hosted"

    log_id = Column(BIGINT, primary_key=True)
    target_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    amount = Column(Integer)
    log_time = Column(DATETIME)


class ModNotes(Base):
    __tablename__ = "mod_notes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    moderator_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    note = Column(TEXT)
    note_time = Column(DATETIME)
    hidden = Column(BOOLEAN, default=False)
    who_hid: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    hide_time = Column(DATETIME)


class Sailor(Base):
    __tablename__ = "sailor"

    discord_id: Mapped[BIGINT] = mapped_column(BIGINT, primary_key=True)
    gamertag = Column(TINYTEXT)
    timezone = Column(TINYTEXT)
    award_ping_enabled = Column(BOOLEAN, default=True)
    carpenter_points = Column(Integer, default=0)
    flex_points = Column(Integer, default=0)
    cannoneer_points = Column(Integer, default=0)
    helm_points = Column(Integer, default=0)
    grenadier_points = Column(Integer, default=0)
    surgeon_points = Column(Integer, default=0)
    voyage_count = Column(Integer, default=0)
    hosted_count = Column(Integer, default=0)
    force_carpenter_points = Column(Integer, default=0)
    force_flex_points = Column(Integer, default=0)
    force_cannoneer_points = Column(Integer, default=0)
    force_helm_points = Column(Integer, default=0)
    force_grenadier_points = Column(Integer, default=0)
    force_surgeon_points = Column(Integer, default=0)
    force_voyage_count = Column(Integer, default=0)
    force_hosted_count = Column(Integer, default=0)


class Subclasses(Base):
    __tablename__ = "subclasses"

    id = Column(Integer, primary_key=True, autoincrement=True)
    author_id = Column(BIGINT)
    log_link = Column(TINYTEXT)
    target_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"))
    subclass = Column(TINYTEXT)
    log_time = Column(DATETIME)


class Voyages(Base):
    __tablename__ = "voyages"

    log_id = Column(BIGINT, primary_key=True)
    target_id: Mapped[BIGINT] = mapped_column(ForeignKey("sailor.discord_id"), primary_key=True)
    log_time = Column(DATETIME)


def create_tables():
    try:
        log.info("Attempting to create all tables")
        Base.metadata.create_all(engine)
    except Exception as e:
        log.error("Failed to create tables: %s", e)


if __name__ == '__main__':
    create_tables()
