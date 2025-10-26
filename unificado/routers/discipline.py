from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    Course,
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
    # Verificar se o curso existe
    course = db.query(Course).filter(Course.id == discipline.course_id).first()
    if not course:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Curso não encontrado'
        )

    # Verfica se o nome da disciplina já esxiste
    discipline_name = (
        db.query(Discipline).filter(Discipline.name == discipline.name).first()
    )
    if discipline_name:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Já existe disciplina com esse nome',
        )

    # Criar a disciplina
    db_discipline = Discipline(
        name=discipline.name, course_id=discipline.course_id
    )
    db.add(db_discipline)
    db.commit()
    db.refresh(db_discipline)

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

    response_data = {
        'id': db_discipline.id,
        'name': db_discipline.name,
        'course_id': db_discipline.course_id,
        'prerequisites': [prereq.id for prereq in db_discipline.prerequisites],
    }

    return response_data


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
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=404, detail='Disciplina não encontrada'
        )
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
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=404, detail='Disciplina não encontrada'
        )

    # Busca o pré-requisito
    prerequisite = (
        db.query(Discipline).filter(Discipline.id == prerequisite_id).first()
    )
    if not prerequisite:
        raise HTTPException(
            status_code=404, detail='Pré-requisito não encontrado'
        )

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
