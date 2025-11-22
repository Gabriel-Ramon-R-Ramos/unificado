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


# Configurável: lista de tuplas (username, discipline_name, desired_status)
# Edite esta lista para aplicar mais mudanças de status sem alterar a lógica abaixo.
STATUS_UPDATES: Sequence[tuple[str, str, str]] = [
    ("aluno.joao", "Algoritmos e Programação", "concluido"),
    ("aluno.joao", "Estrutura de Dados - Desafios de Programação", "concluido"),
    ("aluno.joao", "Grafos: Teoria e Programação", "concluido"),
    ("aluno.joao", "Introdução aos Compiladores", "concluido"),
    ("aluno.joao", "Programação para Internet", "concluido"),
    ("aluno.joao", "Bancos de Dados Relacionais", "concluido"),
    ("aluno.joao", "Banco de Dados NoSQL", "concluido"),
    ("aluno.joao", "Cálculo Diferencial e Integral 1", "concluido"),
    ("aluno.joao", "Cálculo Diferencial e Integral 2", "concluido"),
    ("aluno.joao", "Álgebra Linear", "concluido"),
    ("aluno.joao", "Física do Movimento", "concluido"),
    ("aluno.joao", "Fenômenos Eletromagnéticos", "concluido"),
    ("aluno.joao", "Aplicações de Eletricidade", "concluido"),
    ("aluno.joao", "Sistemas Operacionais", "concluido"),
    ("aluno.joao", "Redes de Computadores", "concluido"),
    ("aluno.joao", "Programação Distribuída e Paralela / Computação em Nuvem", "concluido"),
    ("aluno.joao", "Engenharia de Software - Desenvolvimento Colaborativo Ágil", "concluido"),
    ("aluno.joao", "Gerenciamento de Projetos de Engenharia", "concluido"),
    ("aluno.joao", "Projeto Integrador: Projetos e Software", "concluido"),
    ("aluno.joao", "Projeto Integrador: Desafios de Programação", "concluido"),
]


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


def _ensure_students_disciplines_present(bind, sid, did, status_default: str = 'pendente'):
    """Ensure an entry exists for student-discipline; do not overwrite existing status."""
    exists = bind.execute(
        sa.text(
            "SELECT 1 FROM students_disciplines WHERE student_id = :sid AND discipline_id = :did LIMIT 1"
        ),
        {"sid": sid, "did": did},
    ).first()
    if not exists:
        bind.execute(
            sa.text(
                "INSERT INTO students_disciplines (student_id, discipline_id, status) VALUES (:sid, :did, :status)"
            ),
            {"sid": sid, "did": did, "status": status_default},
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

        # Adicionar todas as disciplinas do currículo do curso ao estudante (sem sobrescrever status existente)
        curriculum = bind.execute(
            sa.text("SELECT discipline_id FROM course_disciplines WHERE course_id = :cid"), {"cid": course_id}
        ).fetchall()
        for row in curriculum:
            try:
                did = row[0]
            except Exception:
                continue
            _ensure_students_disciplines_present(bind, sp_id, did, 'pendente')

    # Ajustar status de disciplinas considerando pré-requisitos
    # Definir ações via `STATUS_UPDATES` (configurável no topo do arquivo)
    for username, dname, desired_status in STATUS_UPDATES:
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
