"""add notification events and sailor activity baselines

Revision ID: d4a9c1b8e721
Revises: 9f14502433ad
Create Date: 2026-04-05 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4a9c1b8e721"
down_revision: str | None = "9f14502433ad"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "sailor", "last_voyage_at"):
        op.add_column(
            "sailor",
            sa.Column("last_voyage_at", sa.DateTime(), nullable=True),
        )

    if not _has_column(inspector, "sailor", "last_hosting_at"):
        op.add_column(
            "sailor",
            sa.Column("last_hosting_at", sa.DateTime(), nullable=True),
        )

    if "notification_events" not in inspector.get_table_names():
        op.create_table(
            "notification_events",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("notification_type", sa.String(length=64), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("sailor_id", sa.BigInteger(), nullable=False),
            sa.Column("ship_role_id", sa.BigInteger(), nullable=True),
            sa.Column("squad_role_id", sa.BigInteger(), nullable=True),
            sa.Column("source_activity_at", sa.DateTime(), nullable=True),
            sa.Column("source_activity_date", sa.Date(), nullable=False),
            sa.Column("threshold_date", sa.Date(), nullable=False),
            sa.Column("trigger_offset", sa.Integer(), nullable=False),
            sa.Column("scheduled_for_date", sa.Date(), nullable=False),
            sa.Column("destination_channel_id", sa.BigInteger(), nullable=True),
            sa.Column("payload_snapshot", sa.Text(), nullable=True),
            sa.Column("skip_reason", sa.Text(), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("claimed_at", sa.DateTime(), nullable=True),
            sa.Column("delivered_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.ForeignKeyConstraint(["sailor_id"], ["sailor.discord_id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "notification_type",
                "sailor_id",
                "threshold_date",
                "trigger_offset",
                name="uq_notification_events_deduplication",
            ),
        )
        op.create_index(
            "ix_notification_events_status_scheduled_for_date",
            "notification_events",
            ["status", "scheduled_for_date"],
            unique=False,
        )

    op.execute(
        sa.text(
            """
            UPDATE sailor
            SET last_voyage_at = (SELECT MAX(voyages.log_time)
                                  FROM voyages
                                  WHERE voyages.target_id = sailor.discord_id)
            """
        )
    )
    op.execute(
        sa.text(
            """
            UPDATE sailor
            SET last_hosting_at = (SELECT MAX(hosted.log_time)
                                   FROM hosted
                                   WHERE hosted.target_id = sailor.discord_id)
            """
        )
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "notification_events" in inspector.get_table_names():
        op.drop_index(
            "ix_notification_events_status_scheduled_for_date",
            table_name="notification_events",
        )
        op.drop_table("notification_events")

    if _has_column(inspector, "sailor", "last_hosting_at"):
        op.drop_column("sailor", "last_hosting_at")

    if _has_column(inspector, "sailor", "last_voyage_at"):
        op.drop_column("sailor", "last_voyage_at")
