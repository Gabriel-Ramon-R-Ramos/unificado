"""relacionando disciplinas professores alunos

Revision ID: 3aa3a204d952
Revises: 0001
Create Date: 2025-10-12 13:12:22.280334

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3aa3a204d952'
down_revision: Union[str, Sequence[str], None] = '0002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Relacionamento muitos-para-muitos entre estudantes e disciplinas
    if 'students_disciplines' not in inspector.get_table_names():
        op.create_table('students_disciplines',
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('discipline_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['discipline_id'], ['disciplines.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['student_profiles.id'], ),
        sa.PrimaryKeyConstraint('student_id', 'discipline_id')
        )
    
    # Relacionamento muitos-para-muitos entre professores e disciplinas
    if 'teacher_disciplines' not in inspector.get_table_names():
        op.create_table('teacher_disciplines',
        sa.Column('teacher_id', sa.Integer(), nullable=False),
        sa.Column('discipline_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['discipline_id'], ['disciplines.id'], ),
        sa.ForeignKeyConstraint(['teacher_id'], ['teacher_profiles.id'], ),
        sa.PrimaryKeyConstraint('teacher_id', 'discipline_id')
        )
    
    # Tornar nome do curso obrigatório (compatível com SQLite)
    # SQLite não suporta ALTER COLUMN, então verificamos se já é NOT NULL
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.alter_column('name',
                   existing_type=sa.VARCHAR(),
                   nullable=False)
    
    # Dropar índices apenas se existirem
    existing_indexes = {idx['name'] for idx in inspector.get_indexes('courses')}
    if 'ix_courses_id' in existing_indexes:
        op.drop_index(op.f('ix_courses_id'), table_name='courses')
    
    # Tornar nome da disciplina obrigatório (compatível com SQLite)
    with op.batch_alter_table('disciplines', schema=None) as batch_op:
        batch_op.alter_column('name',
                   existing_type=sa.VARCHAR(),
                   nullable=False)
    
    # Gerenciar índices de disciplines com verificação
    discipline_indexes = {idx['name'] for idx in inspector.get_indexes('disciplines')}
    
    if 'ix_disciplines_id' in discipline_indexes:
        op.drop_index(op.f('ix_disciplines_id'), table_name='disciplines')
    if 'ix_disciplines_name' in discipline_indexes:
        op.drop_index(op.f('ix_disciplines_name'), table_name='disciplines')
    
    # Criar índices apenas se não existirem
    if 'ix_disciplines_name' not in discipline_indexes:
        op.create_index(op.f('ix_disciplines_name'), 'disciplines', ['name'], unique=False)
    if 'ix_disciplines_course_id' not in discipline_indexes:
        op.create_index(op.f('ix_disciplines_course_id'), 'disciplines', ['course_id'], unique=False)
    
    # Renomear enrollment_number para ra_number em student_profiles
    student_columns = {col['name'] for col in inspector.get_columns('student_profiles')}
    
    if 'ra_number' not in student_columns:
        op.add_column('student_profiles', sa.Column('ra_number', sa.String(length=50), nullable=True))
    
    # Copiar dados se enrollment_number existir
    if 'enrollment_number' in student_columns and 'ra_number' in student_columns:
        bind.execute(sa.text("UPDATE student_profiles SET ra_number = enrollment_number WHERE enrollment_number IS NOT NULL"))
    
    # Recriar foreign keys
    try:
        op.drop_constraint('student_profiles_user_id_fkey', 'student_profiles', type_='foreignkey')
    except Exception:
        pass  # Constraint pode não existir
    
    op.create_foreign_key(None, 'student_profiles', 'users', ['user_id'], ['id'])
    
    if 'enrollment_number' in student_columns:
        op.drop_column('student_profiles', 'enrollment_number')
    
    # Teacher profiles foreign key
    try:
        op.drop_constraint('teacher_profiles_user_id_fkey', 'teacher_profiles', type_='foreignkey')
    except Exception:
        pass  # Constraint pode não existir
    
    op.create_foreign_key(None, 'teacher_profiles', 'users', ['user_id'], ['id'])


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    
    # Reverter foreign keys para teacher_profiles
    try:
        op.drop_constraint('teacher_profiles_user_id_fkey', 'teacher_profiles', type_='foreignkey')
    except Exception:
        pass  # Constraint pode não existir
    
    try:
        op.create_foreign_key('teacher_profiles_user_id_fkey', 'teacher_profiles', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    except Exception:
        pass
    
    # Reverter mudanças em student_profiles
    student_columns = {col['name'] for col in inspector.get_columns('student_profiles')}
    
    if 'enrollment_number' not in student_columns:
        op.add_column('student_profiles', sa.Column('enrollment_number', sa.VARCHAR(length=50), autoincrement=False, nullable=True))
    
    # Copiar dados de volta se ambas colunas existirem
    if 'ra_number' in student_columns and 'enrollment_number' in student_columns:
        bind.execute(sa.text("UPDATE student_profiles SET enrollment_number = ra_number WHERE ra_number IS NOT NULL"))
    
    # Reverter foreign keys para student_profiles
    try:
        op.drop_constraint('student_profiles_user_id_fkey', 'student_profiles', type_='foreignkey')
    except Exception:
        pass
    
    try:
        op.create_foreign_key('student_profiles_user_id_fkey', 'student_profiles', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    except Exception:
        pass
    
    if 'ra_number' in student_columns:
        op.drop_column('student_profiles', 'ra_number')
    
    # Reverter índices de disciplines
    discipline_indexes = {idx['name'] for idx in inspector.get_indexes('disciplines')}
    
    if 'ix_disciplines_course_id' in discipline_indexes:
        op.drop_index(op.f('ix_disciplines_course_id'), table_name='disciplines')
    if 'ix_disciplines_name' in discipline_indexes:
        op.drop_index(op.f('ix_disciplines_name'), table_name='disciplines')
    
    # Recriar índices antigos
    if 'ix_disciplines_name' not in discipline_indexes:
        op.create_index(op.f('ix_disciplines_name'), 'disciplines', ['name'], unique=True)
    if 'ix_disciplines_id' not in discipline_indexes:
        op.create_index(op.f('ix_disciplines_id'), 'disciplines', ['id'], unique=False)
    
    # Reverter nullable em disciplines (compatível com SQLite)
    with op.batch_alter_table('disciplines', schema=None) as batch_op:
        batch_op.alter_column('name',
                   existing_type=sa.VARCHAR(),
                   nullable=True)
    
    # Recriar índice de courses
    course_indexes = {idx['name'] for idx in inspector.get_indexes('courses')}
    if 'ix_courses_id' not in course_indexes:
        op.create_index(op.f('ix_courses_id'), 'courses', ['id'], unique=False)
    
    # Reverter nullable em courses (compatível com SQLite)
    with op.batch_alter_table('courses', schema=None) as batch_op:
        batch_op.alter_column('name',
                   existing_type=sa.VARCHAR(),
                   nullable=True)
    
    # Dropar tabelas M:N se existirem
    existing_tables = inspector.get_table_names()
    if 'teacher_disciplines' in existing_tables:
        op.drop_table('teacher_disciplines')
    if 'students_disciplines' in existing_tables:
        op.drop_table('students_disciplines')
