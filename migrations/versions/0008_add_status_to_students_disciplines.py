"""add status to students_disciplines

Revision ID: 0008_add_status_to_students_disciplines
Revises: 0007_add_ads_course
Create Date: 2025-11-21 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0008_add_status_to_students_disciplines'
down_revision: Union[str, Sequence[str], None] = '0007_add_ads_course'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Adicionar coluna 'status' se não existir
    cols = {c['name'] for c in inspector.get_columns('students_disciplines')}
    if 'status' not in cols:
        op.add_column('students_disciplines', sa.Column('status', sa.String(length=20), nullable=False, server_default='pendente'))
        # Atualizar linhas existentes para 'pendente' explicitamente
        bind.execute(sa.text("UPDATE students_disciplines SET status = 'pendente' WHERE status IS NULL"))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    cols = {c['name'] for c in inspector.get_columns('students_disciplines')}
    if 'status' in cols:
        op.drop_column('students_disciplines', 'status')
