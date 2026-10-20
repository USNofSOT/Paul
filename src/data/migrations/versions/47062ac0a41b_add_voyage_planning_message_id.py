"""add voyage_planning_message_id

Revision ID: 47062ac0a41b
Revises: 6ffd8525c32d
Create Date: 2026-01-02 18:59:15.395900

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '47062ac0a41b'
down_revision: str | None = '6ffd8525c32d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        table_name="hosted",
        column=sa.Column(
            "voyage_planning_message_id", sa.BigInteger(), nullable=True
        ),
    )


def downgrade() -> None:
    op.drop_column("hosted", "voyage_planning_message_id")
