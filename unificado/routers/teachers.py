from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    TeacherProfile,
    User,
)
from unificado.schemas import (
    TeacherCreate,
    TeacherListPublic,
    TeacherPublic,
    TeacherUpdate,
)
from unificado.security import (
    get_current_user_from_token,
    get_password_hash,
    require_role,
)
from unificado.utils import (
    ensure_teacher_profile,
    get_discipline_or_404,
    get_disciplines_map,
    get_user,
)

router = APIRouter(prefix='/teachers', tags=['Professores'])


@router.post('/', response_model=TeacherPublic)
def create_teacher(
    teacher: TeacherCreate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Criar um novo professor - APENAS ADMIN"""
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

    # Criar o usuário (sempre ativo ao criar)
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
        disciplines_id = list(dict.fromkeys(teacher.disciplines))
        found_map, not_found = get_disciplines_map(db, disciplines_id)
        if found_map:
            teacher_profile.disciplines.extend(list(found_map.values()))
            db.commit()
            db.refresh(teacher_profile)

    # Retornar a instância `user` e deixar o Pydantic serializar
    # via `TeacherPublic` (validador transforma o profile em disciplinas)
    db.refresh(user)
    return user


@router.get('/', response_model=list[TeacherListPublic])
def read_teachers(
    skip: int = 0,
    limit: int = 10,
    show_inactive: bool = False,  # Novo parâmetro para admin ver inativos
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Listar professores - Admin vê todos, Professor vê apenas ele mesmo
    show_inactive: apenas admin pode ver usuários inativos
    """
    if current_user['role'] == 'admin':
        # Admin pode ver todos os professores
        query = db.query(User).filter(User.role == 'teacher')

        # Filtrar por status ativo se necessário
        if not show_inactive:
            query = query.filter(User.is_active.is_(True))

        teachers = query.offset(skip).limit(limit).all()

    elif current_user['role'] == 'teacher':
        # Professor pode ver apenas ele mesmo (se ativo)
        teachers = (
            db.query(User)
            .filter(
                User.role == 'teacher',
                User.id == current_user['id'],
                User.is_active.is_(True),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )
    else:
        # Estudantes não podem ver professores
        raise HTTPException(
            status_code=403,
            detail='Estudantes não têm permissão para visualizar professores',
        )
    result: list[TeacherListPublic] = []
    for teacher in teachers:
        emp = (
            teacher.teacher_profile.employee_number
            if teacher.teacher_profile
            else None
        )
        disciplines_count = (
            len(teacher.teacher_profile.disciplines)
            if (
                teacher.teacher_profile
                and getattr(teacher.teacher_profile, 'disciplines', None)
            )
            else 0
        )
        result.append(
            TeacherListPublic(
                id=teacher.id,
                username=teacher.username,
                email=teacher.email,
                employee_number=emp,
                is_active=teacher.is_active,
                disciplines_count=disciplines_count,
            )
        )
    return result


@router.get(
    '/{teacher_id}',
    response_model=TeacherPublic,
)
def read_teacher(
    teacher_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Buscar professor por ID:
    - Admin pode ver qualquer professor (ativo ou inativo)
    - Professor pode ver apenas ele mesmo (se ativo)
    - Estudante não pode ver professores
    """
    if current_user['role'] == 'student':
        raise HTTPException(
            status_code=403,
            detail='Estudantes não têm permissão para visualizar professores',
        )

    if current_user['role'] == 'teacher' and current_user['id'] != teacher_id:
        raise HTTPException(
            status_code=403,
            detail='Professores só podem visualizar seus próprios dados',
        )

    # Buscar professor (admin pode ver inativos)
    require_active = current_user['role'] != 'admin'
    teacher = get_user(
        db, teacher_id, role='teacher', require_active=require_active
    )
    return teacher


@router.patch(
    '/{teacher_id}',
    response_model=TeacherPublic,
)
def update_teacher(
    teacher_id: int,
    teacher: TeacherUpdate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Atualizar dados do professor - APENAS ADMIN"""
    user = get_user(db, teacher_id, role='teacher', require_active=True)

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


@router.patch(
    '/{teacher_id}/disciplines/{discipline_id}',
    response_model=TeacherPublic,
)
def add_discipline_to_teacher(
    teacher_id: int,
    discipline_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Associa uma disciplina a um professor - APENAS ADMIN"""
    # Validar disciplina e buscar professor
    discipline = get_discipline_or_404(db, discipline_id)
    teacher = get_user(db, teacher_id, role='teacher', require_active=True)
    tp = ensure_teacher_profile(teacher)

    # Verificar se a disciplina já está associada
    if discipline in tp.disciplines:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina já está associada ao professor',
        )

    # Adicionar a disciplina
    tp.disciplines.append(discipline)
    db.commit()
    db.refresh(teacher)

    return teacher


@router.patch(
    '/{teacher_id}/remove-discipline/{discipline_id}',
    summary='Remover disciplina do professor',
    response_model=TeacherPublic,
)
def remove_discipline_from_teacher(
    teacher_id: int,
    discipline_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Remove uma disciplina de um professor - APENAS ADMIN"""
    discipline = get_discipline_or_404(db, discipline_id)
    teacher = get_user(db, teacher_id, role='teacher', require_active=True)
    tp = ensure_teacher_profile(teacher)

    # Verificar se a disciplina está associada
    if discipline not in tp.disciplines:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina não está associada ao professor',
        )

    # Remover a disciplina
    tp.disciplines.remove(discipline)
    db.commit()
    db.refresh(teacher)

    return teacher
