"""Voyage types, and more counts

Revision ID: 6ffd8525c32d
Revises:
Create Date: 2025-02-08 18:25:02.342079

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6ffd8525c32d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        table_name="hosted",
        column=sa.Column(
            "fish_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        table_name="hosted",
        column=sa.Column(
            "ancient_coin_count", sa.Integer(), nullable=False, server_default="0"
        ),
    )
    op.add_column(
        table_name="hosted",
        column=sa.Column(
            "voyage_type",
            sa.Enum(
                "UNKNOWN",
                "SKIRMISH",
                "PATROL",
                "ADVENTURE",
                "CONVOY",
                name="voyage_type",
            ),
            nullable=False,
            server_default="UNKNOWN",
        ),
    )


def downgrade() -> None:
    op.drop_column("hosted", "voyage_type")
    op.drop_column("hosted", "ancient_coin_count")
    op.drop_column("hosted", "fish_count")
