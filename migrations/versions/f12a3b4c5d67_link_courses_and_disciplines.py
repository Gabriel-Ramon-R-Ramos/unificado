"""Link courses and disciplines

Revision ID: f12a3b4c5d67
Revises: e86d6eb564a6
Create Date: 2024-12-30 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f12a3b4c5d67'
down_revision: Union[str, None] = 'e86d6eb564a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Link courses and disciplines via course_disciplines table."""
    bind = op.get_bind()
    
    # Primeiro, buscar o curso de Engenharia da Computação (deve ter sido criado na migração 0002)
    course_result = bind.execute(sa.text("SELECT id FROM courses WHERE name = :name LIMIT 1"), 
                                {"name": "Engenharia da Computação"}).first()
    
    if not course_result:
        # Se não existe, criar o curso
        bind.execute(sa.text("INSERT INTO courses (name) VALUES (:name)"), 
                    {"name": "Engenharia da Computação"})
        course_result = bind.execute(sa.text("SELECT id FROM courses WHERE name = :name LIMIT 1"), 
                                    {"name": "Engenharia da Computação"}).first()
    
    if course_result is None:
        raise RuntimeError("Failed to create or find Engenharia da Computação course")
    
    course_id = course_result[0]
    
    # Buscar todas as disciplinas que não estão linkadas a nenhum curso
    disciplines_result = bind.execute(sa.text("SELECT id, name FROM disciplines")).fetchall()
    
    for discipline_id, discipline_name in disciplines_result:
        # Verificar se já existe relacionamento
        existing_relationship = bind.execute(
            sa.text(
                "SELECT 1 FROM course_disciplines "
                "WHERE course_id = :course_id AND discipline_id = :discipline_id"
            ),
            {"course_id": course_id, "discipline_id": discipline_id}
        ).first()
        
        if not existing_relationship:
            # Criar relacionamento
            bind.execute(
                sa.text(
                    "INSERT INTO course_disciplines (course_id, discipline_id) "
                    "VALUES (:course_id, :discipline_id)"
                ),
                {"course_id": course_id, "discipline_id": discipline_id}
            )
            print(f"Linked discipline '{discipline_name}' to course 'Engenharia da Computação'")


def downgrade() -> None:
    """Remove course-discipline links for Engenharia da Computação."""
    bind = op.get_bind()
    
    # Buscar o curso de Engenharia da Computação
    course_result = bind.execute(sa.text("SELECT id FROM courses WHERE name = :name LIMIT 1"), 
                                {"name": "Engenharia da Computação"}).first()
    
    if course_result:
        course_id = course_result[0]
        
        # Remover todos os relacionamentos do curso
        bind.execute(
            sa.text("DELETE FROM course_disciplines WHERE course_id = :course_id"),
            {"course_id": course_id}
        )
        
        print("Removed all course-discipline links for 'Engenharia da Computação'")