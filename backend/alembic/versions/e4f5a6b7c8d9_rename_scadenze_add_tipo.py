"""rename scadenze_contratto to scadenze, add tipo_scadenza and descrizione

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-03-25 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'e4f5a6b7c8d9'
down_revision: Union[str, None] = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rinomina la tabella (preserva tutti i constraint esistenti)
    op.rename_table('scadenze_contratto', 'scadenze')

    # 2. Aggiunge nuove colonne (batch per SQLite compat)
    with op.batch_alter_table('scadenze', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                'tipo_scadenza',
                sa.String(50),
                nullable=False,
                server_default='contratto',
            )
        )
        batch_op.add_column(
            sa.Column(
                'descrizione',
                sa.Text(),
                nullable=True,
            )
        )


def downgrade() -> None:
    with op.batch_alter_table('scadenze', schema=None) as batch_op:
        batch_op.drop_column('descrizione')
        batch_op.drop_column('tipo_scadenza')
    op.rename_table('scadenze', 'scadenze_contratto')
