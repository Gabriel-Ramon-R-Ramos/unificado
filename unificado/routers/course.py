from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    Course,
)
from unificado.schemas import (
    CourseCreate,
    CoursePublic,
)
from unificado.security import (
    get_current_user_from_token,
    require_role,
)

router = APIRouter(prefix='/courses', tags=['Cursos'])


@router.post(
    '/',
    response_model=CoursePublic,
    dependencies=[Depends(require_role('admin'))],
)
def create_course(
    course: CourseCreate,
    db: Session = Depends(get_session),
):
    """Criar um novo curso"""
    db_course = Course(name=course.name)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@router.get('/', response_model=list[CoursePublic])
def read_courses(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Listar todos os cursos -
    Disponível para todos os usuários autenticados"""
    courses = db.query(Course).offset(skip).limit(limit).all()
    return courses


@router.get(
    '/{course_id}',
    response_model=CoursePublic,
)
def read_course(
    course_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Busca um curso específico pelo ID -
    Disponível para todos os usuários autenticados"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail='Curso não encontrado')
    return course


@router.get(
    '/{course_id}/disciplines',
    response_model=list,
)
def read_course_disciplines(
    course_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """Lista todas as disciplinas de um curso específico"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail='Curso não encontrado')

    # Retornar disciplinas do curso
    disciplines = []
    for discipline in course.curriculum:
        disciplines.append({
            'id': discipline.id,
            'name': discipline.name,
            'course_ids': [c.id for c in discipline.courses],
            'prerequisites': [p.id for p in discipline.prerequisites],
        })

    return disciplines
