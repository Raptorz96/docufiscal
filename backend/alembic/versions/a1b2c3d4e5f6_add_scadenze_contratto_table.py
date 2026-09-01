"""add scadenze_contratto table

Revision ID: a1b2c3d4e5f6
Revises: 82c0b75b057e
Create Date: 2026-03-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '82c0b75b057e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'scadenze_contratto',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('cliente_id', sa.Integer(), nullable=False),
        sa.Column('data_inizio', sa.Date(), nullable=True),
        sa.Column('data_scadenza', sa.Date(), nullable=True),
        sa.Column('durata', sa.String(length=100), nullable=True),
        sa.Column('rinnovo_automatico', sa.Boolean(), nullable=True),
        sa.Column('preavviso_disdetta', sa.String(length=200), nullable=True),
        sa.Column('canone', sa.String(length=100), nullable=True),
        sa.Column('parti_coinvolte', sa.JSON(), nullable=True),
        sa.Column('clausole_chiave', sa.JSON(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('verificato', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['cliente_id'], ['clienti.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['documento_id'], ['documenti.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('documento_id'),
    )
    op.create_index(op.f('ix_scadenze_contratto_id'), 'scadenze_contratto', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_scadenze_contratto_id'), table_name='scadenze_contratto')
    op.drop_table('scadenze_contratto')
