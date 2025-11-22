from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from unificado.database import get_session
from unificado.models import (
    Course,
    Discipline,
    StudentProfile,
    User,
)
from unificado.schemas import (
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

    # Criar usuário + perfil + associações em uma transação atômica
    # Validar IDs de disciplinas solicitados antes de associar
    requested_ids: set[int] = set()
    if student.disciplines:
        requested_ids = set(student.disciplines)
        found = (
            db.query(Discipline).filter(Discipline.id.in_(requested_ids)).all()
        )
        found_ids = {d.id for d in found}
        missing = requested_ids - found_ids
        if missing:
            raise HTTPException(
                status_code=HTTPStatus.BAD_REQUEST,
                detail={
                    'msg': 'Algumas disciplinas não foram encontradas',
                    'missing_ids': list(missing),
                },
            )
    # Preparar IDs de disciplinas a serem associadas
    # (união de explicitadas + do curso)
    disciplines_to_assign_ids: set[int] = set()
    if student.disciplines:
        disciplines_to_assign_ids |= requested_ids

    course = None
    if getattr(student, 'course_id', None):
        course = (
            db.query(Course).filter(Course.id == student.course_id).first()
        )
        if not course:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Curso não encontrado',
            )
        if getattr(course, 'curriculum', None):
            disciplines_to_assign_ids |= {d.id for d in course.curriculum}

    # Usar transaction block para garantir atomicidade
    try:
        with db.begin():
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

            # Buscar e associar disciplinas (todos de uma vez)
            if disciplines_to_assign_ids:
                disciplines = (
                    db.query(Discipline)
                    .filter(Discipline.id.in_(disciplines_to_assign_ids))
                    .all()
                )
                student_profile.disciplines.extend(disciplines)

        # Após commit automático, atualizar instâncias
        db.refresh(user)
        if user.student_profile:
            db.refresh(user.student_profile)
    except Exception:
        # Qualquer erro dentro da transação vira 500
        raise

    # Retornar o objeto User; o Pydantic model `StudentPublic` fará
    # a extração dos dados relacionados (incluindo disciplinas)
    return user


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
    # Retornar instâncias do modelo SQLAlchemy diretamente para que o
    # Pydantic `StudentPublic` (com `from_attributes=True`) faça a extração
    # e validação — isso evita problemas com construção manual que acarreta
    # validação rígida de `EmailStr` quando e-mails de seed
    # podem ser inválidos.
    return students


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
        course = db.query(Course).filter(Course.id == new_course_id).first()
        if not course:
            raise HTTPException(
                status_code=HTTPStatus.NOT_FOUND,
                detail='Curso não encontrado',
            )
        # Atualizar course_id e adicionar disciplinas do curso
        # (sem remover as existentes)
        user.student_profile.course_id = new_course_id
        db.flush()
        if getattr(course, 'curriculum', None):
            existing_ids = {d.id for d in user.student_profile.disciplines}
            for disc in course.curriculum:
                if disc.id not in existing_ids:
                    user.student_profile.disciplines.append(disc)

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
    # (comparar por id para ser robusto)
    if any(d.id == discipline.id for d in student.student_profile.disciplines):
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

    # Verificar se a disciplina está associada (comparar por id)
    if not any(
        d.id == discipline.id for d in student.student_profile.disciplines
    ):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Esta disciplina não está associada ao estudante',
        )

    # Remover a disciplina
    student.student_profile.disciplines.remove(discipline)
    db.commit()
    db.refresh(student)

    return student
