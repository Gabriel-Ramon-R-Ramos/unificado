from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from unificado.database import get_session
from unificado.models import (
    User,
)
from unificado.schemas import (
    UserPublic,
)
from unificado.security import (
    get_current_user_from_token,
    require_role,
)
from unificado.utils import get_user

router = APIRouter(prefix='/users', tags=['Usuários'])


@router.get('/me', response_model=UserPublic)
def get_current_user_info(
    current_user: dict = Depends(get_current_user_from_token),
):
    """
    Endpoint protegido - retorna informações do usuário logado
    Requer token JWT válido
    """
    return UserPublic(
        id=current_user['id'],
        username=current_user['username'],
        email=current_user.get('email'),
        role=current_user['role'],
        is_active=True,
    )


@router.get('/')
def list_all_users(
    show_inactive: bool = False,
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_session),
    _: dict = Depends(require_role('admin')),
):
    """
    Listar todos os usuários
    """
    query = db.query(User)

    if not show_inactive:
        query = query.filter(User.is_active.is_(True))

    users = query.offset(skip).limit(limit).all()

    users_serialized = [
        UserPublic(
            id=user.id,
            username=user.username,
            email=user.email,
            role=user.role,
            is_active=user.is_active,
        )
        for user in users
    ]

    return {
        'users': users_serialized,
        'total': query.count(),
        'skip': skip,
        'limit': limit,
        'showing_inactive': show_inactive,
    }


@router.patch('/{user_id}/toggle-active')
def toggle_user_active_status(
    user_id: int,
    db: Session = Depends(get_session),
    current_user: dict = Depends(require_role('admin')),
):
    """
    Ativar/Desativar usuário (Soft Delete)
    """
    user = get_user(db, user_id, require_active=False)

    # Não permitir desativar o próprio usuário admin
    if user.id == current_user['id'] and user.role == 'admin':
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Não é possível desativar seu próprio usuário admin',
        )

    # Alternar status
    user.is_active = not user.is_active
    db.commit()
    db.refresh(user)

    action = 'ativado' if user.is_active else 'desativado'

    return {
        'message': f'Usuário {action} com sucesso',
        'user': {
            'id': user.id,
            'username': user.username,
            'role': user.role,
            'is_active': user.is_active,
        },
    }
