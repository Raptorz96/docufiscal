"""add contratto_id to scadenze_contratto, make documento_id nullable

Revision ID: c2d3e4f5a6b7
Revises: b1c2d3e4f5a6
Create Date: 2026-03-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2d3e4f5a6b7'
down_revision: Union[str, None] = 'b1c2d3e4f5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility (batch recreates the table).
    # On PostgreSQL, Alembic issues real ALTER statements instead.
    with op.batch_alter_table('scadenze_contratto', schema=None) as batch_op:
        # 1. Make documento_id nullable (was NOT NULL)
        batch_op.alter_column(
            'documento_id',
            existing_type=sa.Integer(),
            nullable=True,
        )

        # 2. Add contratto_id column
        batch_op.add_column(
            sa.Column('contratto_id', sa.Integer(), nullable=True)
        )

        # 3. FK from contratto_id → contratti.id with CASCADE
        batch_op.create_foreign_key(
            'fk_scadenze_contratto_contratto_id',
            'contratti',
            ['contratto_id'],
            ['id'],
            ondelete='CASCADE',
        )

        # 4. UNIQUE constraint on contratto_id (one scadenza per contratto)
        batch_op.create_unique_constraint(
            'uq_scadenze_contratto_contratto_id',
            ['contratto_id'],
        )


def downgrade() -> None:
    with op.batch_alter_table('scadenze_contratto', schema=None) as batch_op:
        batch_op.drop_constraint('uq_scadenze_contratto_contratto_id', type_='unique')
        batch_op.drop_constraint('fk_scadenze_contratto_contratto_id', type_='foreignkey')
        batch_op.drop_column('contratto_id')
        batch_op.alter_column(
            'documento_id',
            existing_type=sa.Integer(),
            nullable=False,
        )
