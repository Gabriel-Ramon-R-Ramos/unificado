from typing import List, Literal, Optional

import sqlalchemy as sa
from pydantic import BaseModel, EmailStr, model_validator
from sqlalchemy.orm import object_session

from unificado.models import students_disciplines

# ===== SCHEMAS DE CURSOS =====


class CourseCreate(BaseModel):
    name: str


class CoursePublic(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ===== SCHEMAS DE DISCIPLINAS =====


class DisciplineCreate(BaseModel):
    name: str
    course_ids: Optional[List[int]] = []  # Lista de IDs de cursos (N:N)
    prerequisites: Optional[List[int]] = []


class DisciplinePublic(BaseModel):
    id: int
    name: str
    course_ids: List[int] = []  # Lista de IDs dos cursos (N:N)
    prerequisites: List[int] = []  # Lista de IDs das disciplinas pré-requisito
    status: Optional[str] = (
        None  # status por estudante quando aplicado (ex: 'pendente')
    )

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_related_ids(cls, values):
        if hasattr(values, '__dict__'):
            prerequisites_list = []
            if hasattr(values, 'prerequisites') and values.prerequisites:
                prerequisites_list = [
                    prereq.id for prereq in values.prerequisites
                ]

            course_ids_list = []
            if hasattr(values, 'courses') and values.courses:
                course_ids_list = [course.id for course in values.courses]

            return {
                'id': values.id,
                'name': values.name,
                'course_ids': course_ids_list,
                'prerequisites': prerequisites_list,
            }
        return values


# ===== SCHEMAS DE ESTUDANTES =====


class StudentCreate(BaseModel):
    """Criar estudante completo (user + profile)

    @Attributes
        username: nome de usuário (obrigatório)
        email: email (opcional)
        password: senha (obrigatório)
        ra_number: número de registro acadêmico (opcional)
        disciplines: lista de IDs das disciplinas (opcional)
    """

    username: str
    email: Optional[EmailStr] = None
    password: str
    ra_number: Optional[str] = None
    disciplines: Optional[list[int]] = None  # IDs das disciplinas
    course_id: Optional[int] = (
        None  # ID do curso (opcional) para atribuir grade/currículo
    )


class StudentUpdate(BaseModel):
    """Atualizar dados do estudante (user + profile)

    @Attributes
        username: nome de usuário (opcional)
        email: email (opcional)
        ra_number: número de registro acadêmico (opcional)
    """

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    ra_number: Optional[str] = None
    course_id: Optional[int] = None


class StudentPublic(BaseModel):
    """Estudante completo (user + profile) - SEM senha

    @Attributes
        id: ID do usuário
        username: nome de usuário
        email: email (opcional)
        is_active: se o usuário está ativo
        ra_number: número de registro acadêmico (opcional)
        disciplines: lista de disciplinas associadas ao estudante
    """

    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    ra_number: Optional[str] = None
    disciplines: List[DisciplinePublic] = []
    course: Optional[CoursePublic] = None

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_student_data(cls, values):
        # Saídas rápidas para reduzir níveis de aninhamento
        if not hasattr(values, '__dict__'):
            return values

        profile = getattr(values, 'student_profile', None)
        # Se não houver profile, devolver o mínimo sem disciplinas
        if not profile:
            return {
                'id': values.id,
                'username': values.username,
                'email': values.email,
                'is_active': values.is_active,
                'ra_number': None,
                'disciplines': [],
                'course': None,
            }

        disciplines_list: list[dict] = []
        session = object_session(values)

        if getattr(profile, 'disciplines', None):
            for disc in profile.disciplines:
                status = 'pendente'
                if (
                    session is not None
                    and getattr(profile, 'id', None) is not None
                ):
                    try:
                        row = session.execute(
                            sa.select(students_disciplines.c.status).where(
                                students_disciplines.c.student_id
                                == profile.id,
                                students_disciplines.c.discipline_id
                                == disc.id,
                            )
                        ).first()
                        if row and row[0] is not None:
                            status = row[0]
                    except Exception:
                        # fallback para pendente
                        pass

                disciplines_list.append({
                    'id': disc.id,
                    'name': disc.name,
                    'course_ids': [c.id for c in disc.courses]
                    if getattr(disc, 'courses', None)
                    else [],
                    'prerequisites': [p.id for p in disc.prerequisites]
                    if disc.prerequisites
                    else [],
                    'status': status,
                })

        course = getattr(profile, 'course', None)
        course_data = (
            {'id': course.id, 'name': course.name} if course else None
        )

        return {
            'id': values.id,
            'username': values.username,
            'email': values.email,
            'is_active': values.is_active,
            'ra_number': profile.ra_number if profile else None,
            'disciplines': disciplines_list,
            'course': course_data,
        }


class StudentListPublic(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    ra_number: Optional[str] = None
    course: Optional[CoursePublic] = None
    disciplines_count: int = 0

    class Config:
        from_attributes = True


# ===== SCHEMAS DE PROFESSORES =====


class TeacherCreate(BaseModel):
    """Criar professor completo (user + profile)

    @Attributes
        username: nome de usuário (obrigatório)
        email: email (opcional)
        password: senha (obrigatório)
        employee_number: número de registro do funcionário (opcional)
        disciplines: lista de IDs das disciplinas (opcional)
    """

    username: str
    email: Optional[EmailStr] = None
    password: str
    employee_number: Optional[str] = None
    disciplines: Optional[list[int]] = None  # IDs das disciplinas


class TeacherUpdate(BaseModel):
    """Atualizar dados do professor (user + profile)

    @Attributes
        username: nome de usuário (opcional)
        email: email (opcional)
        employee_number: número de registro do funcionário (opcional)
    """

    username: Optional[str] = None
    email: Optional[EmailStr] = None
    employee_number: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherPublic(BaseModel):
    """Professor completo (user + profile) - SEM senha

    @Attributes
        id: ID do usuário
        username: nome de usuário
        email: email (opcional)
        is_active: se o usuário está ativo
        employee_number: número de registro do funcionário (opcional)
        disciplines: lista de disciplinas associadas ao professor
    """

    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    employee_number: Optional[str] = None
    disciplines: List[DisciplinePublic] = []

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_teacher_data(cls, values):
        if hasattr(values, '__dict__'):
            disciplines_list = []
            if hasattr(values, 'teacher_profile') and values.teacher_profile:
                if hasattr(values.teacher_profile, 'disciplines'):
                    disciplines_list = [
                        {
                            'id': disc.id,
                            'name': disc.name,
                            'course_ids': [c.id for c in disc.courses]
                            if getattr(disc, 'courses', None)
                            else [],
                            'prerequisites': [p.id for p in disc.prerequisites]
                            if disc.prerequisites
                            else [],
                        }
                        for disc in values.teacher_profile.disciplines
                    ]

            return {
                'id': values.id,
                'username': values.username,
                'email': values.email,
                'is_active': values.is_active,
                'employee_number': values.teacher_profile.employee_number
                if values.teacher_profile
                else None,
                'disciplines': disciplines_list,
            }
        return values


class TeacherListPublic(BaseModel):
    id: int
    username: str
    email: Optional[EmailStr] = None
    is_active: bool
    employee_number: Optional[str] = None
    disciplines_count: int = 0

    class Config:
        from_attributes = True


# ===== SCHEMAS DE ADMINISTRADORES =====


class AdminCreate(BaseModel):
    """Criar admin/coordenador

    @Attributes
        username: nome de usuário (obrigatório)
        email: email (opcional)
        password: senha (obrigatório)
    """

    username: str
    email: Optional[EmailStr] = None
    password: str


# ===== SCHEMAS DE USUÁRIOS GENÉRICOS =====


class UserPublic(BaseModel):
    """Schema básico de usuário (sem dados de perfil)

    @Attributes
        id: ID do usuário
        username: nome de usuário
        email: email (opcional)
        role: papel do usuário (student, teacher, admin)
        is_active: se o usuário está ativo"""

    id: int
    username: str
    email: Optional[str] = None
    role: Literal['student', 'teacher', 'admin']
    is_active: bool

    class Config:
        from_attributes = True


class PasswordChange(BaseModel):
    """Para trocar senha (qualquer usuário)

    @Attributes
        current_password: senha atual (obrigatório)
        new_password: nova senha (obrigatório)
    """

    current_password: str
    new_password: str


# ===== SCHEMAS DE AUTENTICAÇÃO =====


class Token(BaseModel):
    """Resposta do endpoint de login com token JWT

    @Attributes
        access_token: token JWT para autenticação
        token_type: tipo do token (sempre "bearer")
        user: dados básicos do usuário logado
    """

    access_token: str
    token_type: str
    user: UserPublic


class TokenData(BaseModel):
    """Dados extraídos do token JWT para validação

    @Attributes
        username: nome de usuário extraído do token
        user_id: ID do usuário extraído do token
        role: papel do usuário (student, teacher, admin)
    """

    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[Literal['student', 'teacher', 'admin']] = None
