"""add course_id to student_profiles and seed teachers/students

Revision ID: 0006_add_profiles_seed
Revises: f12a3b4c5d67
Create Date: 2025-11-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os


# revision identifiers, used by Alembic.
revision: str = '0006_add_profiles_seed'
down_revision: Union[str, Sequence[str], None] = 'f12a3b4c5d67'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _read_env_var(name: str) -> str:
    val = os.environ.get(name)
    if val:
        return val
    env_path = os.path.join(os.getcwd(), '.env')
    try:
        with open(env_path, 'r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' not in line:
                    continue
                k, v = line.split('=', 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == name:
                    return v
    except Exception:
        pass
    return ''


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # 1) Adicionar coluna course_id (nullable) em student_profiles
    student_columns = {col['name'] for col in inspector.get_columns('student_profiles')}
    if 'course_id' not in student_columns:
        op.add_column('student_profiles', sa.Column('course_id', sa.Integer(), nullable=True))
        # criar foreign key e índice
        try:
            op.create_foreign_key(op.f('student_profiles_course_id_fkey'), 'student_profiles', 'courses', ['course_id'], ['id'])
        except Exception:
            pass
        try:
            op.create_index(op.f('ix_student_profiles_course_id'), 'student_profiles', ['course_id'], unique=False)
        except Exception:
            pass

    # 2) Inserir alguns professores e alunos padrão e linkar com disciplinas existentes
    # Ler senhas do .env ou variáveis de ambiente (se fornecidas)
    teacher1_password = _read_env_var('TEACHER1_PASSWORD') or _read_env_var('PROF1_PASSWORD') or 'teacher1'
    teacher2_password = _read_env_var('TEACHER2_PASSWORD') or 'teacher2'
    student1_password = _read_env_var('STUDENT1_PASSWORD') or 'student1'
    student2_password = _read_env_var('STUDENT2_PASSWORD') or 'student2'

    try:
        from unificado.security import get_password_hash
    except Exception:
        raise RuntimeError(
            "Password hashing function not available: ensure `unificado.security.get_password_hash` is importable when running migrations"
        )

    def _ensure_user(username: str, email: str, raw_password: str, role: str) -> int:
        existing = bind.execute(sa.text("SELECT id FROM users WHERE username = :u LIMIT 1"), {"u": username}).first()
        if existing:
            return existing[0]

        ph = get_password_hash(raw_password)
        bind.execute(
            sa.text(
                "INSERT INTO users (username, email, password_hash, role, is_active) VALUES (:u, :e, :ph, :r, True)"
            ),
            {"u": username, "e": email, "ph": ph, "r": role},
        )
        new = bind.execute(sa.text("SELECT id FROM users WHERE username = :u LIMIT 1"), {"u": username}).first()
        if not new:
            raise RuntimeError(f"Failed to create or retrieve user '{username}' after INSERT")
        return new[0]

    def _link_teacher(username: str, employee_number: str, disciplines: Sequence[str]):
        user_id = _ensure_user(username, f"{username}@local.com", teacher1_password if username == 'prof.alves' else teacher2_password, 'teacher')
        # criar perfil de professor se não existir
        existing_tp = bind.execute(sa.text("SELECT id FROM teacher_profiles WHERE user_id = :uid LIMIT 1"), {"uid": user_id}).first()
        if not existing_tp:
            bind.execute(sa.text("INSERT INTO teacher_profiles (user_id, employee_number) VALUES (:uid, :emp)"), {"uid": user_id, "emp": employee_number})
            existing_tp = bind.execute(sa.text("SELECT id FROM teacher_profiles WHERE user_id = :uid LIMIT 1"), {"uid": user_id}).first()
        if not existing_tp:
            raise RuntimeError(f"Failed to create or retrieve teacher_profile for user_id {user_id}")
        tp_id = existing_tp[0]

        # linkar disciplinas
        for dname in disciplines:
            disc = bind.execute(sa.text("SELECT id FROM disciplines WHERE name = :n LIMIT 1"), {"n": dname}).first()
            if disc:
                did = disc[0]
                exists_rel = bind.execute(sa.text("SELECT 1 FROM teacher_disciplines WHERE teacher_id = :tid AND discipline_id = :did"), {"tid": tp_id, "did": did}).first()
                if not exists_rel:
                    bind.execute(sa.text("INSERT INTO teacher_disciplines (teacher_id, discipline_id) VALUES (:tid, :did)"), {"tid": tp_id, "did": did})

    def _link_student(username: str, ra_number: str, disciplines: Sequence[str], course_name: str | None = None):
        user_id = _ensure_user(username, f"{username}@local.com", student1_password if username == 'aluno.joao' else student2_password, 'student')
        # criar perfil de estudante se não existir
        existing_sp = bind.execute(sa.text("SELECT id FROM student_profiles WHERE user_id = :uid LIMIT 1"), {"uid": user_id}).first()
        if not existing_sp:
            # obter course_id se solicitado
            course_id = None
            if course_name:
                c = bind.execute(sa.text("SELECT id FROM courses WHERE name = :n LIMIT 1"), {"n": course_name}).first()
                if c:
                    course_id = c[0]

            bind.execute(sa.text("INSERT INTO student_profiles (user_id, ra_number, course_id) VALUES (:uid, :ra, :cid)"), {"uid": user_id, "ra": ra_number, "cid": course_id})
            existing_sp = bind.execute(sa.text("SELECT id FROM student_profiles WHERE user_id = :uid LIMIT 1"), {"uid": user_id}).first()
        if not existing_sp:
            raise RuntimeError(f"Failed to create or retrieve student_profile for user_id {user_id}")
        sp_id = existing_sp[0]

        # linkar disciplinas
        for dname in disciplines:
            disc = bind.execute(sa.text("SELECT id FROM disciplines WHERE name = :n LIMIT 1"), {"n": dname}).first()
            if disc:
                did = disc[0]
                exists_rel = bind.execute(sa.text("SELECT 1 FROM students_disciplines WHERE student_id = :sid AND discipline_id = :did"), {"sid": sp_id, "did": did}).first()
                if not exists_rel:
                    bind.execute(sa.text("INSERT INTO students_disciplines (student_id, discipline_id) VALUES (:sid, :did)"), {"sid": sp_id, "did": did})

    # Exemplo de seeds (ajuste nomes conforme necessário)
    _link_teacher('prof.alves', 'EMP001', ['Algoritmos e Programação', 'Estrutura de Dados - Desafios de Programação'])
    _link_teacher('prof.silva', 'EMP002', ['Grafos: Teoria e Programação', 'Introdução aos Compiladores'])

    # Students linked to Engenharia da Computação course (se existir)
    _link_student('aluno.joao', '2024001', ['Algoritmos e Programação'], course_name='Engenharia da Computação')
    _link_student('aluna.maria', '2024002', ['Estrutura de Dados - Desafios de Programação'], course_name='Engenharia da Computação')


def downgrade() -> None:
    bind = op.get_bind()

    # Remover os usuários criados pelo upgrade
    for uname in ['prof.alves', 'prof.silva', 'aluno.joao', 'aluna.maria']:
        bind.execute(sa.text("DELETE FROM users WHERE username = :u"), {"u": uname})

    # Remover coluna course_id
    inspector = sa.inspect(bind)
    student_columns = {col['name'] for col in inspector.get_columns('student_profiles')}
    if 'course_id' in student_columns:
        try:
            op.drop_constraint(op.f('student_profiles_course_id_fkey'), 'student_profiles', type_='foreignkey')
        except Exception:
            pass
        try:
            op.drop_index(op.f('ix_student_profiles_course_id'), table_name='student_profiles')
        except Exception:
            pass
        try:
            op.drop_column('student_profiles', 'course_id')
        except Exception:
            pass
