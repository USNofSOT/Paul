"""add sla and cosa training tracking

Revision ID: f6b1e2d4c9a7
Revises: d4a9c1b8e721
Create Date: 2026-04-05 13:30:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6b1e2d4c9a7"
down_revision: str | None = "d4a9c1b8e721"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        table_name="training_records",
        column=sa.Column(
            "sla_training_points", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        table_name="training_records",
        column=sa.Column(
            "cosa_training_points", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE training
                MODIFY COLUMN training_type ENUM(
                'NRC',
                'ST',
                'NETC',
                'JLA',
                'SNLA',
                'SLA',
                'COSA',
                'OCS',
                'SOCS'
                ) NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            """
            ALTER TABLE training
                MODIFY COLUMN training_type ENUM(
                'NRC',
                'ST',
                'NETC',
                'JLA',
                'SNLA',
                'OCS',
                'SOCS'
                ) NOT NULL
            """
        )
    )
    op.drop_column("training_records", "cosa_training_points")
    op.drop_column("training_records", "sla_training_points")
