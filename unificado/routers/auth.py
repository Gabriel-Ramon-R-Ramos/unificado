from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    StudentProfile,
    TeacherProfile,
    User,
)
from unificado.schemas import (
    Token,
    UserPublic,
)
from unificado.security import (
    create_access_token,
    verify_password,
)

router = APIRouter(prefix='/login', tags=['Autenticação'], )


@router.post('/', response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_session),
):
    """
    Login flexível OAuth2 que aceita no campo 'username':
    - Username: admin
    - Email: admin@local.com
    - RA: 202301001 (estudantes)
    - Número de funcionário: FUNC001 (professores)

    Campos obrigatórios:
    - username: qualquer identificador acima
    - password: senha do usuário
    - client_id: qualquer valor (ex: 'web')
    """
    user = None
    identifier = form_data.username.strip()

    # Tentar encontrar usuário por diferentes métodos
    # 1. Por username
    user = db.scalar(select(User).where(User.username == identifier))

    # 2. Por email (se não encontrou por username)
    if not user:
        user = db.scalar(select(User).where(User.email == identifier))

    # 3. Por RA (se for estudante)
    if not user:
        student_profile = db.scalar(
            select(StudentProfile).where(
                StudentProfile.ra_number == identifier
            )
        )
        if student_profile:
            user = student_profile.user

    # 4. Por número de funcionário (se for professor)
    if not user:
        teacher_profile = db.scalar(
            select(TeacherProfile).where(
                TeacherProfile.employee_number == identifier
            )
        )
        if teacher_profile:
            user = teacher_profile.user

    # Verificar se usuário existe
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Credenciais inválidas',
        )

    # Verificar senha
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Credenciais inválidas',
        )

    # Verificar se usuário está ativo
    if not user.is_active:
        raise HTTPException(
            status_code=HTTPStatus.UNAUTHORIZED,
            detail='Usuário inativo',
        )

    # Gerar token JWT com informações completas do usuário
    token_data = {
        'sub': str(user.id),  # Subject (ID do usuário) - deve ser string
        'username': user.username,
        'role': user.role,
        'email': user.email,
        'is_active': user.is_active,
    }

    return Token(
        access_token=create_access_token(token_data),
        token_type='bearer',
        user=UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        ),
    )
