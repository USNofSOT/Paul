"""update rank_id columns to bigint

Revision ID: 714174f5cb32
Revises: afc3160331ca
Create Date: 2026-06-11 02:05:52.355704

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '714174f5cb32'
down_revision: Union[str, None] = 'afc3160331ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('hosted', 'host_rank_id', existing_type=sa.Integer(), type_=sa.BIGINT(), existing_nullable=True)
    op.alter_column('voyages', 'participant_rank_id', existing_type=sa.Integer(), type_=sa.BIGINT(),
                    existing_nullable=True)
    op.alter_column('log_rank_history', 'rank_id', existing_type=sa.Integer(), type_=sa.BIGINT(),
                    existing_nullable=False)
    op.alter_column('sailor', 'current_rank_id', existing_type=sa.Integer(), type_=sa.BIGINT(), existing_nullable=True)


def downgrade() -> None:
    op.alter_column('hosted', 'host_rank_id', existing_type=sa.BIGINT(), type_=sa.Integer(), existing_nullable=True)
    op.alter_column('voyages', 'participant_rank_id', existing_type=sa.BIGINT(), type_=sa.Integer(),
                    existing_nullable=True)
    op.alter_column('log_rank_history', 'rank_id', existing_type=sa.BIGINT(), type_=sa.Integer(),
                    existing_nullable=False)
    op.alter_column('sailor', 'current_rank_id', existing_type=sa.BIGINT(), type_=sa.Integer(), existing_nullable=True)
