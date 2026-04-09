"""add exact notification schedule times

Revision ID: a8d9f3c4b217
Revises: f6b1e2d4c9a7
Create Date: 2026-04-09 12:00:00.000000

"""

from collections.abc import Sequence
from datetime import datetime, time, timedelta

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a8d9f3c4b217"
down_revision: str | None = "f6b1e2d4c9a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

NOTIFICATION_EVENTS_TABLE = "notification_events"
DEDUPLICATION_CONSTRAINT = "uq_notification_events_deduplication"
LEGACY_SCHEDULE_INDEX = "ix_notification_events_status_scheduled_for_date"
EXACT_SCHEDULE_INDEX = "ix_notification_events_status_scheduled_for_at"

# Keep migrations self-contained so later config changes do not affect history.
REQUIREMENT_DAYS_BY_TYPE = {
    "NO_VOYAGE_REMINDER": 28,
    "NO_HOSTING_REMINDER": 14,
}


def _get_inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _get_column(inspector: sa.Inspector, table_name: str, column_name: str) -> dict | None:
    return next(
        (column for column in inspector.get_columns(table_name) if column["name"] == column_name),
        None,
    )


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_unique_constraint(
        inspector: sa.Inspector,
        table_name: str,
        constraint_name: str,
) -> bool:
    return any(
        constraint["name"] == constraint_name
        for constraint in inspector.get_unique_constraints(table_name)
    )


def _resolve_threshold_at(
        notification_type: str,
        source_activity_at: datetime | None,
        threshold_date,
) -> datetime:
    if source_activity_at is None:
        return datetime.combine(threshold_date, time.min)

    return source_activity_at + timedelta(
        days=REQUIREMENT_DAYS_BY_TYPE.get(notification_type, 0)
    )


def _backfill_exact_schedule_times() -> None:
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
            """
            SELECT id, notification_type, source_activity_at, threshold_date, trigger_offset
            FROM notification_events
            """
        )
    ).mappings()

    for row in rows:
        threshold_at = _resolve_threshold_at(
            row["notification_type"],
            row["source_activity_at"],
            row["threshold_date"],
        )
        scheduled_for_at = threshold_at + timedelta(days=row["trigger_offset"])

        bind.execute(
            sa.text(
                """
                UPDATE notification_events
                SET threshold_at     = :threshold_at,
                    scheduled_for_at = :scheduled_for_at
                WHERE id = :event_id
                """
            ),
            {
                "event_id": row["id"],
                "threshold_at": threshold_at,
                "scheduled_for_at": scheduled_for_at,
            },
        )


def upgrade() -> None:
    inspector = _get_inspector()
    if not _has_table(inspector, NOTIFICATION_EVENTS_TABLE):
        return

    if _get_column(inspector, NOTIFICATION_EVENTS_TABLE, "threshold_at") is None:
        op.add_column(
            NOTIFICATION_EVENTS_TABLE,
            sa.Column("threshold_at", sa.DateTime(), nullable=True),
        )

    if _get_column(inspector, NOTIFICATION_EVENTS_TABLE, "scheduled_for_at") is None:
        op.add_column(
            NOTIFICATION_EVENTS_TABLE,
            sa.Column("scheduled_for_at", sa.DateTime(), nullable=True),
        )

    _backfill_exact_schedule_times()

    inspector = _get_inspector()
    threshold_at_column = _get_column(inspector, NOTIFICATION_EVENTS_TABLE, "threshold_at")
    if threshold_at_column is not None and threshold_at_column["nullable"]:
        op.alter_column(
            NOTIFICATION_EVENTS_TABLE,
            "threshold_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

    scheduled_for_at_column = _get_column(inspector, NOTIFICATION_EVENTS_TABLE, "scheduled_for_at")
    if scheduled_for_at_column is not None and scheduled_for_at_column["nullable"]:
        op.alter_column(
            NOTIFICATION_EVENTS_TABLE,
            "scheduled_for_at",
            existing_type=sa.DateTime(),
            nullable=False,
        )

    inspector = _get_inspector()
    if _has_index(inspector, NOTIFICATION_EVENTS_TABLE, LEGACY_SCHEDULE_INDEX):
        op.drop_index(LEGACY_SCHEDULE_INDEX, table_name=NOTIFICATION_EVENTS_TABLE)

    if _has_unique_constraint(inspector, NOTIFICATION_EVENTS_TABLE, DEDUPLICATION_CONSTRAINT):
        op.drop_constraint(
            DEDUPLICATION_CONSTRAINT,
            NOTIFICATION_EVENTS_TABLE,
            type_="unique",
        )

    op.create_unique_constraint(
        DEDUPLICATION_CONSTRAINT,
        NOTIFICATION_EVENTS_TABLE,
        ["notification_type", "sailor_id", "threshold_at", "trigger_offset"],
    )
    op.create_index(
        EXACT_SCHEDULE_INDEX,
        NOTIFICATION_EVENTS_TABLE,
        ["status", "scheduled_for_at"],
        unique=False,
    )


def downgrade() -> None:
    inspector = _get_inspector()
    if not _has_table(inspector, NOTIFICATION_EVENTS_TABLE):
        return

    if _has_index(inspector, NOTIFICATION_EVENTS_TABLE, EXACT_SCHEDULE_INDEX):
        op.drop_index(EXACT_SCHEDULE_INDEX, table_name=NOTIFICATION_EVENTS_TABLE)

    if _has_unique_constraint(inspector, NOTIFICATION_EVENTS_TABLE, DEDUPLICATION_CONSTRAINT):
        op.drop_constraint(
            DEDUPLICATION_CONSTRAINT,
            NOTIFICATION_EVENTS_TABLE,
            type_="unique",
        )

    op.create_unique_constraint(
        DEDUPLICATION_CONSTRAINT,
        NOTIFICATION_EVENTS_TABLE,
        ["notification_type", "sailor_id", "threshold_date", "trigger_offset"],
    )
    op.create_index(
        LEGACY_SCHEDULE_INDEX,
        NOTIFICATION_EVENTS_TABLE,
        ["status", "scheduled_for_date"],
        unique=False,
    )

    inspector = _get_inspector()
    if _get_column(inspector, NOTIFICATION_EVENTS_TABLE, "scheduled_for_at") is not None:
        op.drop_column(NOTIFICATION_EVENTS_TABLE, "scheduled_for_at")

    if _get_column(inspector, NOTIFICATION_EVENTS_TABLE, "threshold_at") is not None:
        op.drop_column(NOTIFICATION_EVENTS_TABLE, "threshold_at")
