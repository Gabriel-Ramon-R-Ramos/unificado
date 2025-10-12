from http import HTTPStatus

from fastapi import APIRouter, Depends, FastAPI, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    Course,
    Discipline,
    StudentProfile,
    TeacherProfile,
    User,
)
from unificado.schemas import (
    CourseCreate,
    CoursePublic,
    DisciplineCreate,
    DisciplinePublic,
    StudentCreate,
    StudentPublic,
    StudentUpdate,
    TeacherCreate,
    TeacherPublic,
    TeacherUpdate,
)
from unificado.security import get_password_hash

app = FastAPI(
    title='Rede de Conhecimento',
    description='API para gerenciamento de cursos, disciplinas e usuários',
    version='1.0.0',
    tags_metadata=[
        {
            'name': 'Cursos',
            'description': (
                'Operações relacionadas aos cursos oferecidos pela instituição'
            ),
        },
        {
            'name': 'Disciplinas',
            'description': (
                'Gerenciamento de disciplinas e seus pré-requisitos'
            ),
        },
        {
            'name': 'Estudantes',
            'description': 'Cadastro e gerenciamento de estudantes',
        },
        {
            'name': 'Professores',
            'description': 'Cadastro e gerenciamento de professores',
        },
        {
            'name': 'Usuários',
            'description': 'Operações gerais de usuários e autenticação',
        },
        {
            'name': 'Sistema',
            'description': 'Informações gerais do sistema e saúde da API',
        },
    ],
)

router_v1 = APIRouter(prefix='/api/v1')


# ==== CURSOS ====
@router_v1.post('/courses/', response_model=CoursePublic, tags=['Cursos'])
def create_course(course: CourseCreate, db: Session = Depends(get_session)):
    db_course = Course(name=course.name)
    db.add(db_course)
    db.commit()
    db.refresh(db_course)
    return db_course


@router_v1.get('/courses/', response_model=list[CoursePublic], tags=['Cursos'])
def read_courses(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_session)
):
    courses = db.query(Course).offset(skip).limit(limit).all()
    return courses


@router_v1.get(
    '/courses/{course_id}', response_model=CoursePublic, tags=['Cursos']
)
def read_course(course_id: int, db: Session = Depends(get_session)):
    """Busca um curso específico pelo ID"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail='Curso não encontrado')
    return course


# === DISCIPLINAS ===
@router_v1.post(
    '/disciplines/', response_model=DisciplinePublic, tags=['Disciplinas']
)
def create_discipline(
    discipline: DisciplineCreate, db: Session = Depends(get_session)
):
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


@router_v1.get(
    '/disciplines/',
    response_model=list[DisciplinePublic],
    tags=['Disciplinas'],
)
def read_disciplines(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_session)
):
    db_disciplines = db.scalars(
        select(Discipline).limit(limit).offset(skip)
    ).all()
    return db_disciplines


@router_v1.get(
    '/disciplines/{discipline_id}',
    response_model=DisciplinePublic,
    tags=['Disciplinas'],
)
def read_discipline_by_id(
    discipline_id: int, db: Session = Depends(get_session)
):
    """Busca uma disciplina específica pelo ID"""
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=404, detail='Disciplina não encontrada'
        )
    return discipline


@router_v1.post(
    '/disciplines/{discipline_id}/prerequisites/{prerequisite_id}',
    response_model=DisciplinePublic,
    tags=['Disciplinas'],
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


# === ESTUDANTES ===
@router_v1.post('/students', response_model=StudentPublic, tags=['Estudantes'])
def create_student(student: StudentCreate, db: Session = Depends(get_session)):
    # Verificar se o username ou email já existe
    existing_user = (
        db.query(User)
        .filter(
            (User.username == student.username) | (User.email == student.email)
        )
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Username ou email já existe',
        )

    # Criar o usuário
    user = User(
        username=student.username,
        email=student.email,
        password_hash=get_password_hash(student.password),
        role='student',
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Criar o perfil do estudante
    student_profile = StudentProfile(
        user_id=user.id,
        ra_number=student.ra_number,
    )
    db.add(student_profile)
    db.commit()
    db.refresh(student_profile)

    if student.disciplines:
        disciplines_id = set(student.disciplines)
        disciplines = (
            db.query(Discipline)
            .filter(Discipline.id.in_(disciplines_id))
            .all()
        )
        student_profile.disciplines.extend(disciplines)
        db.commit()
        db.refresh(student_profile)

    return StudentPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        ra_number=student_profile.ra_number,
        is_active=user.is_active,
        disciplines=[
            DisciplinePublic(
                id=disc.id,
                name=disc.name,
                course_id=disc.course_id,
                prerequisites=[prereq.id for prereq in disc.prerequisites],
            )
            for disc in student_profile.disciplines
        ],
    )


@router_v1.get(
    '/students/', response_model=list[StudentPublic], tags=['Estudantes']
)
def read_students(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_session)
):
    students = (
        db.query(User)
        .filter(User.role == 'student')
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        StudentPublic(
            id=student.id,
            username=student.username,
            email=student.email,
            ra_number=student.student_profile.ra_number
            if student.student_profile
            else None,
            is_active=student.is_active,
        )
        for student in students
    ]


@router_v1.get(
    '/students/{student_id}', response_model=StudentPublic, tags=['Estudantes']
)
def read_student(student_id: int, db: Session = Depends(get_session)):
    student = (
        db.query(User)
        .filter(User.id == student_id, User.role == 'student')
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Estudante não encontrado',
        )
    return student


@router_v1.patch(
    '/students/{student_id}', response_model=StudentPublic, tags=['Estudantes']
)
def update_student(
    student_id: int, student: StudentUpdate, db: Session = Depends(get_session)
):
    user = (
        db.query(User)
        .filter(User.id == student_id, User.role == 'student')
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Estudante não encontrado',
        )

    # Atualizanado nome do usuário
    if student.username is not None:
        existing = (
            db.query(User)
            .filter(User.username == student.username, User.id != student_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Nome de usuário já existe',
            )

        user.username = student.username

    # Atualizando email do usuário
    if student.email is not None:
        existing = (
            db.query(User)
            .filter(User.email == student.email, User.id != student_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='E-mail de usuário já existe',
            )

        user.email = student.email

    if student.ra_number is not None and user.student_profile:
        user.student_profile.ra_number = student.ra_number

    db.commit()
    db.refresh(user)

    return user


@router_v1.patch(
    '/students/{student_id}/disciplines/{discipline_id}',
    response_model=StudentPublic,
    tags=['Estudantes'],
)
def add_disciplines(
    student_id: int, discipline_id: int, db: Session = Depends(get_session)
):
    """Associa uma disciplina a um estudante"""
    # Buscar disciplina
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )

    # Buscar estudante e carregar o perfil
    student = (
        db.query(User)
        .filter(User.id == student_id, User.role == 'student')
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Estudante não encontrado',
        )

    # Verificar se o estudante tem perfil
    if not student.student_profile:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Perfil do estudante não encontrado',
        )

    # Verificar se a disciplina já está associada
    if discipline in student.student_profile.disciplines:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina já está associada ao estudante',
        )

    # Adicionar a disciplina
    student.student_profile.disciplines.append(discipline)
    db.commit()
    db.refresh(student)

    return student


@router_v1.patch(
    '/students/{student_id}/remove-discipline/{discipline_id}',
    tags=['Estudantes'],
    summary='Remover disciplina do estudante',
    response_model=StudentPublic,
)
def remove_discipline(
    student_id: int, discipline_id: int, db: Session = Depends(get_session)
):
    """Remove uma disciplina de um estudante"""
    # Buscar disciplina
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )

    # Buscar estudante
    student = (
        db.query(User)
        .filter(User.id == student_id, User.role == 'student')
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Estudante não encontrado',
        )

    # Verificar se o estudante tem perfil
    if not student.student_profile:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Perfil do estudante não encontrado',
        )

    # Verificar se a disciplina está associada
    if discipline not in student.student_profile.disciplines:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina não está associada ao estudante',
        )

    # Remover a disciplina
    student.student_profile.disciplines.remove(discipline)
    db.commit()
    db.refresh(student)

    return student


# === PROFESSORES ===
@router_v1.post(
    '/teachers/', response_model=TeacherPublic, tags=['Professores']
)
def create_teacher(teacher: TeacherCreate, db: Session = Depends(get_session)):
    """Criar um novo professor"""
    # Verificar se o username ou email já existe
    existing_user = (
        db.query(User)
        .filter(
            (User.username == teacher.username) | (User.email == teacher.email)
        )
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Username ou email já existe',
        )

    # Criar o usuário
    user = User(
        username=teacher.username,
        email=teacher.email,
        password_hash=get_password_hash(teacher.password),
        role='teacher',
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Criar o perfil do professor
    teacher_profile = TeacherProfile(
        user_id=user.id,
        employee_number=teacher.employee_number,
    )
    db.add(teacher_profile)
    db.commit()
    db.refresh(teacher_profile)

    # Associar disciplinas se fornecidas
    if teacher.disciplines:
        disciplines_id = set(teacher.disciplines)
        disciplines = (
            db.query(Discipline)
            .filter(Discipline.id.in_(disciplines_id))
            .all()
        )
        teacher_profile.disciplines.extend(disciplines)
        db.commit()
        db.refresh(teacher_profile)

    return TeacherPublic(
        id=user.id,
        username=user.username,
        email=user.email,
        employee_number=teacher_profile.employee_number,
        is_active=user.is_active,
        disciplines=[
            DisciplinePublic(
                id=disc.id,
                name=disc.name,
                course_id=disc.course_id,
                prerequisites=[prereq.id for prereq in disc.prerequisites],
            )
            for disc in teacher_profile.disciplines
        ],
    )


@router_v1.get(
    '/teachers/', response_model=list[TeacherPublic], tags=['Professores']
)
def read_teachers(
    skip: int = 0, limit: int = 10, db: Session = Depends(get_session)
):
    """Listar todos os professores"""
    teachers = (
        db.query(User)
        .filter(User.role == 'teacher')
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [
        TeacherPublic(
            id=teacher.id,
            username=teacher.username,
            email=teacher.email,
            employee_number=teacher.teacher_profile.employee_number
            if teacher.teacher_profile
            else None,
            is_active=teacher.is_active,
        )
        for teacher in teachers
    ]


@router_v1.get(
    '/teachers/{teacher_id}',
    response_model=TeacherPublic,
    tags=['Professores'],
)
def read_teacher(teacher_id: int, db: Session = Depends(get_session)):
    """Buscar professor por ID"""
    teacher = (
        db.query(User)
        .filter(User.id == teacher_id, User.role == 'teacher')
        .first()
    )
    if not teacher:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado',
        )
    return teacher


@router_v1.patch(
    '/teachers/{teacher_id}',
    response_model=TeacherPublic,
    tags=['Professores'],
)
def update_teacher(
    teacher_id: int, teacher: TeacherUpdate, db: Session = Depends(get_session)
):
    """Atualizar dados do professor"""
    user = (
        db.query(User)
        .filter(User.id == teacher_id, User.role == 'teacher')
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado',
        )

    # Atualizando nome do usuário
    if teacher.username is not None:
        existing = (
            db.query(User)
            .filter(User.username == teacher.username, User.id != teacher_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Nome de usuário já existe',
            )
        user.username = teacher.username

    # Atualizando email do usuário
    if teacher.email is not None:
        existing = (
            db.query(User)
            .filter(User.email == teacher.email, User.id != teacher_id)
            .first()
        )
        if existing:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='E-mail de usuário já existe',
            )
        user.email = teacher.email

    # Atualizando número de funcionário
    if teacher.employee_number is not None and user.teacher_profile:
        user.teacher_profile.employee_number = teacher.employee_number

    # Atualizando status ativo
    if teacher.is_active is not None:
        user.is_active = teacher.is_active

    db.commit()
    db.refresh(user)

    return user


@router_v1.patch(
    '/teachers/{teacher_id}/disciplines/{discipline_id}',
    response_model=TeacherPublic,
    tags=['Professores'],
)
def add_discipline_to_teacher(
    teacher_id: int, discipline_id: int, db: Session = Depends(get_session)
):
    """Associa uma disciplina a um professor"""
    # Buscar disciplina
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )

    # Buscar professor
    teacher = (
        db.query(User)
        .filter(User.id == teacher_id, User.role == 'teacher')
        .first()
    )
    if not teacher:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado',
        )

    # Verificar se o professor tem perfil
    if not teacher.teacher_profile:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Perfil do professor não encontrado',
        )

    # Verificar se a disciplina já está associada
    if discipline in teacher.teacher_profile.disciplines:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina já está associada ao professor',
        )

    # Adicionar a disciplina
    teacher.teacher_profile.disciplines.append(discipline)
    db.commit()
    db.refresh(teacher)

    return teacher


@router_v1.patch(
    '/teachers/{teacher_id}/remove-discipline/{discipline_id}',
    tags=['Professores'],
    summary='Remover disciplina do professor',
    response_model=TeacherPublic,
)
def remove_discipline_from_teacher(
    teacher_id: int, discipline_id: int, db: Session = Depends(get_session)
):
    """Remove uma disciplina de um professor"""
    # Buscar disciplina
    discipline = (
        db.query(Discipline).filter(Discipline.id == discipline_id).first()
    )
    if not discipline:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não encontrada',
        )

    # Buscar professor
    teacher = (
        db.query(User)
        .filter(User.id == teacher_id, User.role == 'teacher')
        .first()
    )
    if not teacher:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Professor não encontrado',
        )

    # Verificar se o professor tem perfil
    if not teacher.teacher_profile:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Perfil do professor não encontrado',
        )

    # Verificar se a disciplina está associada
    if discipline not in teacher.teacher_profile.disciplines:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina não está associada ao professor',
        )

    # Remover a disciplina
    teacher.teacher_profile.disciplines.remove(discipline)
    db.commit()
    db.refresh(teacher)

    return teacher


# === SISTEMA ===
@router_v1.get('/', tags=['Sistema'])
def read_root():
    return {'message': 'Rede de Conhecimento API funcionando!'}


app.include_router(router_v1)
