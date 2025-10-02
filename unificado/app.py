from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import Course, Discipline
from unificado.schemas import (
    CourseCreate,
    CoursePublic,
    DisciplineCreate,
    DisciplinePublic,
)

app = FastAPI(title='Rede de Conhecimento')


@app.post('/courses/', response_model=CoursePublic)
def create_course(course: CourseCreate, db: Session = Depends(get_session)):
    db_course = Course(name=course.name)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@app.get('/courses/', response_model=list[CoursePublic])
def read_courses(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_session)
):
    courses = db.query(Course).offset(skip).limit(limit).all()
    return courses


@app.get('/courses/{course_id}', response_model=CoursePublic)
def read_course(course_id: int, db: Session = Depends(get_session)):
    """Busca um curso específico pelo ID"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail='Curso não encontrado')
    return course


@app.post('/disciplines/', response_model=DisciplinePublic)
def create_discipline(
    discipline: DisciplineCreate, db: Session = Depends(get_session)
):
    # Verificar se o curso existe
    course = db.query(Course).filter(Course.id == discipline.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail='Curso não encontrado')

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


@app.get('/disciplines/', response_model=list[DisciplinePublic])
def read_disciplines(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_session)
):
    db_disciplines = db.scalars(
        select(Discipline).limit(limit).offset(skip)
    ).all()
    return db_disciplines


@app.get('/disciplines/{discipline_id}', response_model=DisciplinePublic)
def read_discipline(discipline_id: int, db: Session = Depends(get_session)):
    """Busca uma disciplina específica pelo ID"""
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=404, detail='Disciplina não encontrada'
        )
    return discipline


@app.post(
    '/disciplines/{discipline_id}/prerequisites/{prerequisite_id}',
    response_model=DisciplinePublic,
)
def add_prerequisite(
    discipline_id: int,
    prerequisite_id: int,
    db: Session = Depends(get_session),
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


@app.get('/')
def read_root():
    return {'message': 'Rede de Conhecimento API funcionando!'}
