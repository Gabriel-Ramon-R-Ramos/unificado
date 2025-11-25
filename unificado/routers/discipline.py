from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    Discipline,
)
from unificado.schemas import (
    DisciplineCreate,
    DisciplinePublic,
)
from unificado.security import (
    get_current_user_from_token,
    require_role,
)
from unificado.utils import get_course_or_404, get_discipline_or_404

router = APIRouter(prefix='/disciplines', tags=['Disciplinas'])


@router.post(
    '/',
    response_model=DisciplinePublic,
)
def create_discipline(
    discipline: DisciplineCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Criar uma nova disciplina - APENAS ADMIN"""
    # Verificar se os cursos existem (se fornecidos)
    courses = []
    if discipline.course_ids:
        for course_id in discipline.course_ids:
            course = get_course_or_404(db, course_id)
            courses.append(course)

    # Verificar se o nome da disciplina já existe
    discipline_name = (
        db.query(Discipline).filter(Discipline.name == discipline.name).first()
    )
    if discipline_name:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Já existe disciplina com esse nome',
        )

    # Criar a disciplina (sem course_id)
    db_discipline = Discipline(name=discipline.name)
    db.add(db_discipline)
    db.commit()
    db.refresh(db_discipline)

    # Associar aos cursos
    for course in courses:
        db_discipline.courses.append(course)

    # Processar pré-requisitos se fornecidos
    if discipline.prerequisites:
        for prerequisite_id in discipline.prerequisites:
            prerequisite = (
                db.query(Discipline)
                .filter(Discipline.id == prerequisite_id)
                .first()
            )
            if prerequisite:
                db_discipline.prerequisites.append(prerequisite)

    db.commit()
    db.refresh(db_discipline)

    return db_discipline


@router.get(
    '/',
    response_model=list[DisciplinePublic],
)
def read_disciplines(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Listar todas as disciplinas -
    Disponível para todos os usuários autenticados"""
    db_disciplines = db.scalars(
        select(Discipline).limit(limit).offset(skip)
    ).all()
    return db_disciplines


@router.get(
    '/{discipline_id}',
    response_model=DisciplinePublic,
)
def read_discipline_by_id(
    discipline_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Busca uma disciplina específica pelo ID -
    Disponível para todos os usuários autenticados"""
    discipline = get_discipline_or_404(db, discipline_id)
    return discipline


@router.post(
    '/{discipline_id}/prerequisites/{prerequisite_id}',
    response_model=DisciplinePublic,
)
def add_prerequisite(
    discipline_id: int,
    prerequisite_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Adiciona uma disciplina como pré-requisito de outra"""
    # Verificar se não está tentando adicionar uma disciplina
    # como pré-requisito de si mesma
    if discipline_id == prerequisite_id:
        raise HTTPException(
            status_code=400,
            detail='Uma disciplina não pode ser pré-requisito de si mesma',
        )

    # Busca a disciplina principal
    discipline = get_discipline_or_404(db, discipline_id)
    prerequisite = get_discipline_or_404(db, prerequisite_id)

    # Verificar se o pré-requisito já existe
    if prerequisite in discipline.prerequisites:
        raise HTTPException(
            status_code=400, detail='Este pré-requisito já foi adicionado'
        )

    # Adiciona o pré-requisito
    discipline.prerequisites.append(prerequisite)
    db.commit()
    db.refresh(discipline)

    return discipline


@router.post(
    '/{discipline_id}/courses/{course_id}',
    response_model=DisciplinePublic,
)
def add_discipline_to_course(
    discipline_id: int,
    course_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Associa uma disciplina a um curso"""
    # Buscar a disciplina
    discipline = get_discipline_or_404(db, discipline_id)
    course = get_course_or_404(db, course_id)

    # Verificar se a associação já existe
    if course in discipline.courses:
        raise HTTPException(
            status_code=400, detail='Disciplina já está associada a este curso'
        )

    # Adicionar a associação
    discipline.courses.append(course)
    db.commit()
    db.refresh(discipline)

    return discipline


@router.delete(
    '/{discipline_id}/courses/{course_id}',
    response_model=DisciplinePublic,
)
def remove_discipline_from_course(
    discipline_id: int,
    course_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Remove a associação entre uma disciplina e um curso"""
    # Buscar a disciplina
    discipline = get_discipline_or_404(db, discipline_id)
    course = get_course_or_404(db, course_id)

    # Verificar se a associação existe
    if course not in discipline.courses:
        raise HTTPException(
            status_code=400,
            detail='Disciplina não está associada a este curso',
        )

    # Remover a associação
    discipline.courses.remove(course)
    db.commit()
    db.refresh(discipline)

    return discipline
