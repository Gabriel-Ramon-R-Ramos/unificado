"""create users, profiles and default admin

Revision ID: 0001_create_users_and_profiles_and_admin
Revises: 
Create Date: 2025-10-09 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = '339dbadfaddc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- create users table ---
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('username', sa.String(length=100), nullable=False, unique=True, index=True),
        sa.Column('email', sa.String(length=255), nullable=True, unique=True),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='student'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('1')),
    )

    # --- create student_profiles table ---
    op.create_table(
        'student_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('enrollment_number', sa.String(length=50), nullable=True),
    )

    # --- create teacher_profiles table ---
    op.create_table(
        'teacher_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True),
        sa.Column('employee_number', sa.String(length=50), nullable=True),
    )

    # --- create default admin if ADMIN_PASSWORD provided ---
    def _read_env_var(name: str) -> str:
        # check environment first
        val = os.environ.get(name)
        if val:
            return val
        # fallback: try to read a .env file in the project root (cwd)
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
                    v = v.strip().strip('\"').strip("\'")
                    if k == name:
                        return v
        except Exception:
            pass
        return ''

    admin_password = _read_env_var('ADMIN_PASSWORD')
    admin_email = _read_env_var('ADMIN_EMAIL') or os.environ.get('ADMIN_EMAIL', 'admin@local')

    # do insertion only if password provided and user doesn't exist
    bind = op.get_bind()
    if admin_password:
        existing = bind.execute(sa.text("SELECT id FROM users WHERE username = :u LIMIT 1"), {"u": "admin"}).first()
        if not existing:
            try:
                from unificado.security import get_password_hash
            except Exception:
                raise RuntimeError(
                    "Password hashing function not available: ensure `unificado.security.get_password_hash` "
                    "is importable when running migrations"
                )
            ph = get_password_hash(admin_password)

            bind.execute(
                sa.text(
                    "INSERT INTO users (username, email, password_hash, role, is_active) "
                    "VALUES (:u, :e, :ph, 'admin', 1)"
                ),
                {"u": "admin", "e": admin_email, "ph": ph},
            )


def downgrade() -> None:
    bind = op.get_bind()
    # remove admin user if exists
    bind.execute(sa.text("DELETE FROM users WHERE username = :u AND role = 'admin'"), {"u": "admin"})

    # drop profiles then users
    op.drop_table('teacher_profiles')
    op.drop_table('student_profiles')
    op.drop_table('users')
