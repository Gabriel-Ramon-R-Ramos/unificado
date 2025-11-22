"""update student courses and discipline statuses

Revision ID: 0009_update_students
Revises: 0008_add_status
Create Date: 2025-11-21 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0009_update_students'
down_revision: Union[str, Sequence[str], None] = '0008_add_status'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _ensure_students_disciplines_entry(bind, sid, did, status_val: str):
    existing = bind.execute(
        sa.text(
            "SELECT status FROM students_disciplines WHERE student_id = :sid AND discipline_id = :did LIMIT 1"
        ),
        {"sid": sid, "did": did},
    ).first()
    if existing:
        # atualizar sempre (sobrescrever mesmo que seja igual)
        bind.execute(
            sa.text(
                "UPDATE students_disciplines SET status = :status WHERE student_id = :sid AND discipline_id = :did"
            ),
            {"status": status_val, "sid": sid, "did": did},
        )
    else:
        bind.execute(
            sa.text(
                "INSERT INTO students_disciplines (student_id, discipline_id, status) VALUES (:sid, :did, :status)"
            ),
            {"sid": sid, "did": did, "status": status_val},
        )


def upgrade() -> None:
    bind = op.get_bind()

    # Mapear usernames para novos course_id conforme solicitado
    updates = [
        ("aluno.joao", 1),
        ("aluna.maria", 2),
    ]

    for username, course_id in updates:
        user_row = bind.execute(sa.text("SELECT id FROM users WHERE username = :u LIMIT 1"), {"u": username}).first()
        if not user_row:
            # usuário inexistente: pular
            continue
        user_id = user_row[0]
        sp = bind.execute(sa.text("SELECT id FROM student_profiles WHERE user_id = :uid LIMIT 1"), {"uid": user_id}).first()
        if not sp:
            continue
        sp_id = sp[0]
        # Atualizar course_id do profile
        bind.execute(sa.text("UPDATE student_profiles SET course_id = :cid WHERE id = :spid"), {"cid": course_id, "spid": sp_id})

    # Ajustar status de disciplinas considerando pré-requisitos
    # Definir ações desejadas (username, discipline_name, desired_status)
    actions = [
        ("aluno.joao", "Algoritmos e Programação", 'concluido'),
        ("aluna.maria", "Estrutura de Dados - Desafios de Programação", 'cursando'),
    ]

    for username, dname, desired_status in actions:
        user_row = bind.execute(sa.text("SELECT id FROM users WHERE username = :u LIMIT 1"), {"u": username}).first()
        if not user_row:
            continue
        user_id = user_row[0]
        sp = bind.execute(sa.text("SELECT id FROM student_profiles WHERE user_id = :uid LIMIT 1"), {"uid": user_id}).first()
        if not sp:
            continue
        sp_id = sp[0]

        disc = bind.execute(sa.text("SELECT id FROM disciplines WHERE name = :n LIMIT 1"), {"n": dname}).first()
        if not disc:
            continue
        did = disc[0]

        # Garantir que pré-requisitos estejam Concluídos antes de marcar cursando/concluido
        prereqs = bind.execute(
            sa.text("SELECT prerequisite_id FROM discipline_prerequisites WHERE discipline_id = :did"), {"did": did}
        ).fetchall()
        prereq_ids = [r[0] for r in prereqs] if prereqs else []

        # Para cada pré-requisito, garantir que exista registro com status 'concluido'
        for pid in prereq_ids:
            _ensure_students_disciplines_entry(bind, sp_id, pid, 'concluido')

        # Agora aplicar o status desejado na disciplina alvo
        _ensure_students_disciplines_entry(bind, sp_id, did, desired_status)


def downgrade() -> None:
    bind = op.get_bind()

    # Não fazemos rollback automático de dados sensíveis — operação irreversível via downgrade.
    # Opcionalmente, poderíamos restaurar course_id para NULL e status para 'pendente',
    # mas deixamos downgrade sem ação para evitar perda acidental de informações.
    pass
