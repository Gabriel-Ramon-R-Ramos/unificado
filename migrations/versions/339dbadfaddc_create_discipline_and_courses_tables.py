"""create discipline and courses tables

Revision ID: 339dbadfaddc
Revises: 
Create Date: 2025-10-09 18:53:26.800781

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '339dbadfaddc'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # criar tabela courses
    op.create_table(
        'courses',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, unique=True),
    )
    # criar tabela disciplines
    op.create_table(
        'disciplines',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=False, index=True),
        sa.Column('course_id', sa.Integer(), sa.ForeignKey('courses.id'), nullable=False, index=True),
    )

    # tabela de associação many-to-many
    op.create_table(
        'discipline_prerequisites',
        sa.Column('discipline_id', sa.Integer(), sa.ForeignKey('disciplines.id'), primary_key=True, nullable=False),
        sa.Column('prerequisite_id', sa.Integer(), sa.ForeignKey('disciplines.id'), primary_key=True, nullable=False),
    )


def downgrade() -> None:
    """Downgrade schema."""
    # remover tabela de associação primeiro (dependência)
    op.drop_table('discipline_prerequisites')

    # remover índices e tabela disciplines
    op.drop_index(op.f('ix_disciplines_course_id'), table_name='disciplines')
    op.drop_index(op.f('ix_disciplines_name'), table_name='disciplines')
    op.drop_table('disciplines')

    # remover tabela courses
    op.drop_table('courses')
