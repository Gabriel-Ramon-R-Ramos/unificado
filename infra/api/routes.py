from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from infra.database.database import SessionLocal
from infra.data.models import Discipline
from infra.data.schemas import DisciplineCreate, DisciplineRead
from infra.data.models import Course
from infra.data.schemas import CourseCreate, CourseRead

router = APIRouter()

# Dependência para obter a sessão do banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/courses/", response_model=CourseRead)
def create_course(course: CourseCreate, db: Session = Depends(get_db)):
    db_course = Course(name=course.name)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course

@router.get("/courses/", response_model=list[CourseRead])
def read_courses(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    courses = db.query(Course).offset(skip).limit(limit).all()
    return courses

@router.get("/courses/{course_id}", response_model=CourseRead)
def read_course(course_id: int, db: Session = Depends(get_db)):
    """Busca um curso específico pelo ID"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    return course

@router.post("/disciplines/", response_model=DisciplineRead)
def create_discipline(discipline: DisciplineCreate, db: Session = Depends(get_db)):
    # Verificar se o curso existe
    course = db.query(Course).filter(Course.id == discipline.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    # Criar a disciplina
    db_discipline = Discipline(
        name=discipline.name,
        course_id=discipline.course_id
    )
    db.add(db_discipline)
    db.commit()
    db.refresh(db_discipline)
    
    # Processar pré-requisitos se fornecidos
    warning_messages = []
    if discipline.prerequisites:
        for prerequisite_id in discipline.prerequisites:
            prerequisite = db.query(Discipline).filter(Discipline.id == prerequisite_id).first()
            if prerequisite:
                db_discipline.prerequisites.append(prerequisite)
            else:
                warning_messages.append(f"Pré-requisito com ID {prerequisite_id} não encontrado e não foi adicionado")
        
        db.commit()
        db.refresh(db_discipline)
    
    # Preparar resposta com warnings se houver
    response_data = {
        "id": db_discipline.id,
        "name": db_discipline.name,
        "course_id": db_discipline.course_id,
        "prerequisites": [prereq.id for prereq in db_discipline.prerequisites]
    }
    
    if warning_messages:
        response_data["warnings"] = warning_messages
    
    return response_data

@router.get("/disciplines/", response_model=list[DisciplineRead])
def read_disciplines(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    disciplines = db.query(Discipline).offset(skip).limit(limit).all()
    return disciplines

@router.get("/disciplines/{discipline_id}", response_model=DisciplineRead)
def read_discipline(discipline_id: int, db: Session = Depends(get_db)):
    """Busca uma disciplina específica pelo ID"""
    discipline = db.query(Discipline).filter(Discipline.id == discipline_id).first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
    return discipline

@router.post("/disciplines/{discipline_id}/prerequisites/{prerequisite_id}", response_model=DisciplineRead)
def add_prerequisite(discipline_id: int, prerequisite_id: int, db: Session = Depends(get_db)):
    """Adiciona uma disciplina como pré-requisito de outra"""
    # Verificar se não está tentando adicionar uma disciplina como pré-requisito de si mesma
    if discipline_id == prerequisite_id:
        raise HTTPException(status_code=400, detail="Uma disciplina não pode ser pré-requisito de si mesma")
    
    # Busca a disciplina principal
    discipline = db.query(Discipline).filter(Discipline.id == discipline_id).first()
    if not discipline:
        raise HTTPException(status_code=404, detail="Disciplina não encontrada")
    
    # Busca o pré-requisito
    prerequisite = db.query(Discipline).filter(Discipline.id == prerequisite_id).first()
    if not prerequisite:
        raise HTTPException(status_code=404, detail="Pré-requisito não encontrado")
    
    # Verificar se o pré-requisito já existe
    if prerequisite in discipline.prerequisites:
        raise HTTPException(status_code=400, detail="Este pré-requisito já foi adicionado")
    
    # Adiciona o pré-requisito
    discipline.prerequisites.append(prerequisite)
    db.commit()
    db.refresh(discipline)
    
    return discipline

@router.get("/")
def read_root():
    return {"message": "Rede de Conhecimento API funcionando!"}
