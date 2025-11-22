from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pwdlib import PasswordHash

from unificado.settings import Settings

SECRET_KEY = Settings().SECRET_KEY  # type: ignore
ALGORITHM = Settings().ALGORITHM  # type: ignore
ACCESS_TOKEN_EXPIRE_MINUTES = Settings().ACCESS_TOKEN_EXPIRE_MINUTES  # type: ignore

pwd_context = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/login/')


def get_password_hash(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict):
    """
    Cria um JWT token com informações do usuário

    Args:
        data: Dicionário com dados do usuário:
            - sub: ID do usuário
            - username: nome de usuário
            - role: papel (student, teacher, admin)
            - email: email do usuário (opcional)
    """
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({'exp': expire})
    jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return jwt_token


def decode_access_token(token: str):
    """
    Decodifica e valida um JWT token

    Returns:
        dict: Dados do token decodificado

    Raises:
        HTTPException: Se o token for inválido ou expirado
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token expirado',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    except (jwt.DecodeError, jwt.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token inválido',
            headers={'WWW-Authenticate': 'Bearer'},
        )


def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
):
    """
    Dependency para extrair usuário atual do JWT token

    Returns:
        dict: Dados do usuário do token

    Raises:
        HTTPException: Se token inválido ou usuário não encontrado
    """
    payload = decode_access_token(token)

    # Extrair dados do token
    user_id = payload.get('sub')
    username = payload.get('username')
    role = payload.get('role')

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Token inválido: ID do usuário não encontrado',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # Retornar dados do token (sem consultar DB por performance)
    return {
        'id': int(user_id),  # Converter de volta para int
        'username': username,
        'role': role,
    }


def require_role(*allowed_roles: str):
    """
    Decorator/Dependency para verificar se usuário tem role necessária

    Args:
        allowed_roles: Roles permitidas ('admin', 'teacher', 'student')

    Returns:
        function: Dependency que valida role

    Usage:
        @app.get("/admin-only")
        def admin_endpoint(user = Depends(require_role("admin"))):
            pass

        @app.get("/teacher-or-admin")
        def teacher_endpoint(user = Depends(require_role("teacher", "admin"))):
            pass
    """

    def role_checker(
        current_user: dict = Depends(get_current_user_from_token),
    ):
        user_role = current_user.get('role')

        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f'Acesso negado. Requer role: {", ".join(allowed_roles)}'
                ),
            )

        return current_user

    return role_checker
