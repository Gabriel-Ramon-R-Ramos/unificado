from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    Discipline,
    StudentProfile,
    User,
)
from unificado.schemas import (
    DisciplinePublic,
    StudentCreate,
    StudentPublic,
    StudentUpdate,
)
from unificado.security import (
    get_current_user_from_token,
    get_password_hash,
    require_role,
)

router = APIRouter(prefix='/students', tags=['Estudantes'])


@router.post(
    '/',
    response_model=StudentPublic,
)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Criar um novo estudante - APENAS ADMIN"""
    # Verificar se o username ou email já existe (incluindo usuários inativos)
    existing_user = (
        db.query(User)
        .filter(
            (User.username == student.username) | (User.email == student.email)
        )
        .first()
    )
    if existing_user:
        if existing_user.is_active:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail='Username ou email já existe',
            )
        else:
            # Se o usuário existe mas está inativo, pode reativar
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail=(
                    'Username ou email já existe (usuário inativo).'
                    'Entre em contato com o administrador para reativação.'
                ),
            )

    # Criar o usuário (sempre ativo ao criar)
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


@router.get(
    '/',
    response_model=list[StudentPublic],
)
def read_students(
    skip: int = 0,
    limit: int = 10,
    show_inactive: bool = False,  # Novo parâmetro para admin ver inativos
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('teacher', 'admin')),
):
    """
    Listar estudantes - PROFESSORES E ADMINS
    show_inactive: apenas admin pode ver usuários inativos
    """
    query = db.query(User).filter(User.role == 'student')

    # Filtrar por status ativo
    if not show_inactive or current_user['role'] != 'admin':
        query = query.filter(User.is_active)

    students = query.offset(skip).limit(limit).all()
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


@router.get(
    '/{student_id}',
    response_model=StudentPublic,
)
def read_student(
    student_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Ver dados de estudante específico:
    - Estudantes: apenas próprios dados (se ativo)
    - Professores: qualquer estudante ativo
    - Admins: qualquer estudante (ativo ou inativo)
    """
    user_role = current_user['role']
    user_id = current_user['id']

    # Validar permissões
    if user_role == 'student' and user_id != student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Estudantes só podem acessar seus próprios dados',
        )
    elif user_role not in {'student', 'teacher', 'admin'}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Role não autorizada',
        )

    # Buscar estudante
    query = db.query(User).filter(
        User.id == student_id, User.role == 'student'
    )

    # Apenas admin pode ver usuários inativos
    if user_role != 'admin':
        query = query.filter(User.is_active.is_(True))

    student = query.first()

    if not student:
        if user_role == 'admin':
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Estudante não encontrado',
            )
        else:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Estudante não encontrado ou inativo',
            )
    return student


@router.patch(
    '/{student_id}',
    response_model=StudentPublic,
)
def update_student(
    student_id: int,
    student: StudentUpdate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Atualizar dados de estudante - APENAS ADMIN"""
    user = (
        db.query(User)
        .filter(
            User.id == student_id,
            User.role == 'student',
            User.is_active.is_(
                True
            ),  # Apenas usuários ativos podem ser atualizados
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Estudante ativo não encontrado',
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


@router.patch(
    '/{student_id}/disciplines/{discipline_id}',
    response_model=StudentPublic,
)
def add_disciplines(
    student_id: int,
    discipline_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Associar disciplina a estudante - APENAS ADMIN"""
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
        .filter(
            User.id == student_id,
            User.role == 'student',
            User.is_active.is_(True),  # Apenas usuários ativos
        )
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Estudante ativo não encontrado',
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


@router.patch(
    '/{student_id}/remove-discipline/{discipline_id}',
    summary='Remover disciplina do estudante',
    response_model=StudentPublic,
)
def remove_discipline(
    student_id: int,
    discipline_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Remover disciplina de estudante - APENAS ADMIN"""
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
        .filter(
            User.id == student_id,
            User.role == 'student',
            User.is_active.is_(True),  # Apenas usuários ativos
        )
        .first()
    )
    if not student:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Estudante ativo não encontrado',
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
