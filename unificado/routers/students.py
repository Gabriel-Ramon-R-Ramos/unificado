from http import HTTPStatus
from typing import cast

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from unificado.database import get_session
from unificado.models import (
    StudentProfile,
    User,
    students_disciplines,
)
from unificado.schemas import (
    BatchDisciplineRequest,
    BatchDisciplineResponse,
    CoursePublic,
    DisciplineStatusUpdate,
    StudentCreate,
    StudentListPublic,
    StudentPublic,
    StudentUpdate,
)
from unificado.security import (
    get_current_user_from_token,
    get_password_hash,
    require_role,
)
from unificado.utils import (
    ensure_student_profile,
    get_course_or_404,
    get_discipline_or_404,
    get_disciplines_map,
    get_student,
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
    # Verificar existência do curso (se fornecido)
    course = None
    course_id_val = getattr(student, 'course_id', None)
    if course_id_val is not None:
        course = get_course_or_404(db, course_id_val)

    user = User(
        username=student.username,
        email=student.email,
        password_hash=get_password_hash(student.password),
        role='student',
    )
    db.add(user)
    db.flush()  # assegura que user.id exista

    student_profile = StudentProfile(
        user_id=user.id,
        ra_number=student.ra_number,
        course_id=getattr(student, 'course_id', None),
    )
    db.add(student_profile)

    # Se solicitado, atribuir automaticamente o currículo do curso
    if (
        getattr(student, 'assign_course_curriculum', True)
        and course
        and getattr(course, 'curriculum', None)
    ):
        # adicionar disciplinas do currículo sem duplicar
        existing_ids = {d.id for d in student_profile.disciplines}
        for disc in course.curriculum:
            if disc.id not in existing_ids:
                student_profile.disciplines.append(disc)

    # A confirmação/rollback da transação será feita pelo gerenciador
    # de contexto em `get_session` quando a dependência for finalizada.
    db.refresh(user)
    if user.student_profile:
        db.refresh(user.student_profile)

    # Retornar o objeto User; o Pydantic model `StudentPublic` fará
    # a extração dos dados relacionados (incluindo disciplinas)
    return user


@router.get(
    '/',
    response_model=list[StudentListPublic],
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
    # Eager-loadar perfil e curso para que `StudentPublic`
    # tenha o course disponível
    query = (
        db.query(User)
        .filter(User.role == 'student')
        .options(
            selectinload(User.student_profile).selectinload(
                StudentProfile.course
            )
        )
    )

    # Filtrar por status ativo
    if not show_inactive or current_user['role'] != 'admin':
        query = query.filter(User.is_active)

    students = query.offset(skip).limit(limit).all()

    # Construir uma lista simplificada sem as disciplinas — o detalhamento
    # completo (incluindo disciplinas) fica disponível apenas em
    # GET /students/{id}
    result: list[StudentListPublic] = []
    for s in students:
        ra = None
        course_data = None
        if getattr(s, 'student_profile', None):
            ra = getattr(s.student_profile, 'ra_number', None)
            c = getattr(s.student_profile, 'course', None)
            if c:
                course_data = {'id': c.id, 'name': c.name}

        sp = getattr(s, 'student_profile', None)
        if sp and getattr(sp, 'disciplines', None):
            disciplines_count = len(sp.disciplines)
        else:
            disciplines_count = 0

        result.append(
            StudentListPublic(
                id=s.id,
                username=s.username,
                email=s.email,
                is_active=s.is_active,
                ra_number=ra,
                course=CoursePublic(**course_data) if course_data else None,
                disciplines_count=disciplines_count,
            )
        )

    return result


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
    query = (
        db.query(User)
        .filter(User.id == student_id, User.role == 'student')
        .options(
            selectinload(User.student_profile).selectinload(
                StudentProfile.course
            )
        )
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

    # Atualizar curso do estudante (se fornecido)
    if (
        getattr(student, 'course_id', None) is not None
        and user.student_profile
    ):
        # Validar existência do curso antes de atualizar
        # e adicionar disciplinas
        new_course_id = student.course_id
        if new_course_id is None:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST, detail='Curso inválido'
            )
        course = get_course_or_404(db, new_course_id)
        # Atualizar course_id e adicionar disciplinas do curso
        # (sem remover as existentes)
        sp = user.student_profile
        sp.course_id = new_course_id
        db.flush()
        if getattr(course, 'curriculum', None):
            existing_ids = {d.id for d in sp.disciplines}
            for disc in course.curriculum:
                if disc.id not in existing_ids:
                    sp.disciplines.append(disc)

    db.commit()
    db.refresh(user)

    return user


@router.patch(
    '/{student_id}/disciplines/{discipline_id}',
    response_model=StudentPublic,
    summary='Adicionar disciplina ao estudante',
)
def add_disciplines(
    student_id: int,
    discipline_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Associar disciplina a estudante - APENAS ADMIN"""
    """Associa uma disciplina a um estudante"""
    # Validar disciplina e estudante
    discipline = get_discipline_or_404(db, discipline_id)
    student = get_student(db, student_id, require_active=True)
    sp = ensure_student_profile(student)

    # Verificar se a disciplina já está associada
    # (comparar por id para ser robusto)
    if any(d.id == discipline.id for d in sp.disciplines):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina já está associada ao estudante',
        )

    # Adicionar a disciplina
    sp.disciplines.append(discipline)
    db.commit()
    db.refresh(student)

    return student


@router.post(
    '/{student_id}/disciplines',
    response_model=BatchDisciplineResponse,
    summary='Adicionar múltiplas disciplinas ao estudante',
)
def add_disciplines_batch(
    student_id: int,
    payload: BatchDisciplineRequest,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Associar várias disciplinas a um estudante - APENAS ADMIN

    - Se alguma disciplina não existir, ela é isolada (reportada em
      `not_found`) e as demais são processadas.
    - Disciplinas já associadas são ignoradas e listadas em `skipped`.
    """
    ids = list(dict.fromkeys(payload.discipline_ids))
    if not ids:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma disciplina informada',
        )

    # Buscar disciplinas existentes
    found_map, not_found = get_disciplines_map(db, ids)
    found = list(found_map.values())

    student = get_student(db, student_id, require_active=True)
    sp = ensure_student_profile(student)

    existing_ids = {d.id for d in sp.disciplines}
    skipped: list[int] = []
    to_add = []
    for d in found:
        if d.id in existing_ids:
            skipped.append(d.id)
        else:
            to_add.append(d)

    for d in to_add:
        sp.disciplines.append(d)

    db.commit()
    db.refresh(student)

    return BatchDisciplineResponse(
        student=cast(StudentPublic, student),
        not_found=not_found,
        skipped=skipped,
    )


@router.delete(
    '/{student_id}/disciplines',
    response_model=BatchDisciplineResponse,
    summary='Remover múltiplas disciplinas do estudante',
)
def remove_disciplines_batch(
    student_id: int,
    payload: BatchDisciplineRequest,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Remover várias disciplinas de um estudante - APENAS ADMIN

    - Se alguma disciplina não existir, ela é isolada (reportada em
      `not_found`) e as demais são processadas.
    - Disciplinas que não estiverem associadas são ignoradas e listadas
      em `skipped`.
    """
    ids = list(dict.fromkeys(payload.discipline_ids))
    if not ids:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Nenhuma disciplina informada',
        )

    found_map, not_found = get_disciplines_map(db, ids)
    student = get_student(db, student_id, require_active=True)
    sp = ensure_student_profile(student)

    existing_ids = {d.id for d in sp.disciplines}
    skipped: list[int] = []
    for i in ids:
        if i not in found_map:
            continue
        if i not in existing_ids:
            skipped.append(i)
            continue
        # safe to remove
        sp.disciplines.remove(found_map[i])

    db.commit()
    db.refresh(student)

    return BatchDisciplineResponse(
        student=cast(StudentPublic, student),
        not_found=not_found,
        skipped=skipped,
    )


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
    discipline = get_discipline_or_404(db, discipline_id)
    student = get_student(db, student_id, require_active=True)
    sp = ensure_student_profile(student)

    # Verificar se a disciplina está associada (comparar por id)
    if not any(d.id == discipline.id for d in sp.disciplines):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina não está associada ao estudante',
        )

    # Remover a disciplina
    sp.disciplines.remove(discipline)
    db.commit()
    db.refresh(student)

    return student


@router.patch(
    '/{student_id}/disciplines/{discipline_id}/status',
    response_model=StudentPublic,
)
def update_discipline_status(
    student_id: int,
    discipline_id: int,
    payload: DisciplineStatusUpdate,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """Atualizar status de uma disciplina associada a um estudante.

    - Apenas admins podem alterar o status.
    - Professores e alunos apenas podem visualizar via GET.

    Status possíveis (explicação):
    - `pendente`: disciplina cadastrada para o estudante, ainda não iniciada.
    - `cursando`: estudante está em andamento na disciplina.
    - `concluido`: estudante finalizou e concluiu a disciplina.
    """
    student = get_student(db, student_id, require_active=False)
    sp = ensure_student_profile(student)

    sp_id = sp.id

    # Verificar associação existente (student_id em students_disciplines
    # referencia student_profiles.id)
    row = db.execute(
        sa.select(students_disciplines).where(
            students_disciplines.c.student_id == sp_id,
            students_disciplines.c.discipline_id == discipline_id,
        )
    ).first()
    if not row:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail='Disciplina não associada ao estudante',
        )

    # Atualizar status usando student_profile.id
    # (student_id na tabela de associação refere-se a student_profiles.id)
    db.execute(
        sa.update(students_disciplines)
        .where(
            students_disciplines.c.student_id == sp_id,
            students_disciplines.c.discipline_id == discipline_id,
        )
        .values(status=payload.status)
    )
    db.commit()
    db.refresh(student)

    return student
