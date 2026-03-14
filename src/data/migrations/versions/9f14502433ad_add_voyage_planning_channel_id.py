"""add voyage_planning_channel_id

Revision ID: 9f14502433ad
Revises: 47062ac0a41b
Create Date: 2026-03-14 17:55:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f14502433ad"
down_revision: str | None = "47062ac0a41b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        table_name="hosted",
        column=sa.Column(
            "voyage_planning_channel_id", sa.BigInteger(), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("hosted", "voyage_planning_channel_id")
