from http import HTTPStatus
from typing import Dict, List, Tuple

from fastapi import HTTPException
from sqlalchemy.orm import Session

from unificado.models import Course, Discipline, StudentProfile, User


def get_student(
    db: Session, student_id: int, require_active: bool = True
) -> User:
    """Buscar usuário do tipo 'student'. Levanta 404 se não encontrado.

    `require_active` controla se apenas estudantes ativos são considerados.
    """
    query = db.query(User).filter(
        User.id == student_id, User.role == 'student'
    )
    if require_active:
        query = query.filter(User.is_active.is_(True))
    user = query.first()
    if not user:
        detail = (
            'Estudante ativo não encontrado'
            if require_active
            else 'Estudante não encontrado'
        )
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=detail)
    return user


def ensure_student_profile(user: User) -> StudentProfile:
    """Garantir que o usuário possui `student_profile`.

    Levanta 400 caso contrário.
    """
    sp = getattr(user, 'student_profile', None)
    if sp is None:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Perfil do estudante não encontrado',
        )
    return sp


def get_discipline_or_404(db: Session, discipline_id: int) -> Discipline:
    disc = db.query(Discipline).filter(Discipline.id == discipline_id).first()
    if not disc:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )
    return disc


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Curso não encontrado'
        )
    return course


def get_disciplines_map(
    db: Session, ids: List[int]
) -> Tuple[Dict[int, Discipline], List[int]]:
    """Retorna (mapa_id->Discipline, lista_not_found) dada lista de ids."""
    if not ids:
        return {}, []
    found = db.query(Discipline).filter(Discipline.id.in_(ids)).all()
    found_map: Dict[int, Discipline] = {d.id: d for d in found}
    not_found = [i for i in ids if i not in found_map]
    return found_map, not_found
