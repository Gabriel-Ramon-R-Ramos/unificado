"""add ADS course and link default curriculum

Revision ID: 0007_add_ads_course
Revises: 0006_add_profiles_seed
Create Date: 2025-11-21 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0007_add_ads_course'
down_revision: Union[str, Sequence[str], None] = '0006_add_profiles_seed'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # Criar curso ADS se não existir
    course_name = 'Analise e Desenvolvimento de Sistemas'
    course_result = bind.execute(sa.text("SELECT id FROM courses WHERE name = :name LIMIT 1"), {"name": course_name}).first()
    if not course_result:
        bind.execute(sa.text("INSERT INTO courses (name) VALUES (:name)"), {"name": course_name})
        course_result = bind.execute(sa.text("SELECT id FROM courses WHERE name = :name LIMIT 1"), {"name": course_name}).first()

    if not course_result:
        raise RuntimeError('Failed to create or find ADS course')

    course_id = course_result[0]

    # Lista de disciplinas padrão do curso ADS (algumas compartilhadas com Engenharia,
    # outras específicas). Os nomes devem corresponder aos inseridos na migração de disciplinas.
    ads_disciplines = [
        'Algoritmos e Programação',
        'Estrutura de Dados - Desafios de Programação',
        'Programação para Internet',
        'Bancos de Dados Relacionais',
        'Engenharia de Software - Desenvolvimento Colaborativo Ágil',
        'Projeto Integrador: Projetos e Software',
        'Desenvolvimento Mobile - Jogos para Dispositivos Móveis',
        'Fundamentos de Prototipagem Digital',
        'Vida & Carreira - Comunicação e Liderança',
    ]

    # Vincular cada disciplina ao curso (se ela existir e o relacionamento ainda não existir)
    for dname in ads_disciplines:
        disc = bind.execute(sa.text("SELECT id FROM disciplines WHERE name = :n LIMIT 1"), {"n": dname}).first()
        if not disc:
            # Disciplina não existe na base de dados; pular (migração anterior insere a maioria)
            continue
        did = disc[0]
        exists_rel = bind.execute(
            sa.text(
                "SELECT 1 FROM course_disciplines WHERE course_id = :cid AND discipline_id = :did"
            ),
            {"cid": course_id, "did": did},
        ).first()
        if not exists_rel:
            bind.execute(
                sa.text(
                    "INSERT INTO course_disciplines (course_id, discipline_id) VALUES (:cid, :did)"
                ),
                {"cid": course_id, "did": did},
            )


def downgrade() -> None:
    bind = op.get_bind()

    # Remover relacionamentos e curso ADS
    course_name = 'ADS'
    course_result = bind.execute(sa.text("SELECT id FROM courses WHERE name = :name LIMIT 1"), {"name": course_name}).first()
    if course_result:
        course_id = course_result[0]
        # Remover relacionamentos
        bind.execute(sa.text("DELETE FROM course_disciplines WHERE course_id = :cid"), {"cid": course_id})
        # Remover o curso
        bind.execute(sa.text("DELETE FROM courses WHERE id = :cid"), {"cid": course_id})