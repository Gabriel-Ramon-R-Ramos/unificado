from typing import List, Optional

from pydantic import BaseModel, EmailStr, model_validator

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
    course_id: int
    prerequisites: Optional[List[int]] = []


class DisciplinePublic(BaseModel):
    id: int
    name: str
    course_id: int
    prerequisites: List[int] = []  # Lista de IDs das disciplinas pré-requisito

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_prerequisites_ids(cls, values):
        if hasattr(values, '__dict__'):
            prerequisites_list = []
            if hasattr(values, 'prerequisites') and values.prerequisites:
                prerequisites_list = [
                    prereq.id for prereq in values.prerequisites
                ]

            return {
                'id': values.id,
                'name': values.name,
                'course_id': values.course_id,
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

    class Config:
        from_attributes = True

    @model_validator(mode='before')
    @classmethod
    def extract_student_data(cls, values):
        if hasattr(values, '__dict__'):
            # Extrair disciplinas do relacionamento M:N
            disciplines_list = []
            if hasattr(values, 'student_profile') and values.student_profile:
                if hasattr(values.student_profile, 'disciplines'):
                    disciplines_list = [
                        {
                            'id': disc.id,
                            'name': disc.name,
                            'course_id': disc.course_id,
                            'prerequisites': (
                                [p.id for p in disc.prerequisites]
                                if disc.prerequisites
                                else []
                            ),
                        }
                        for disc in values.student_profile.disciplines
                    ]

            return {
                'id': values.id,
                'username': values.username,
                'email': values.email,
                'is_active': values.is_active,
                'ra_number': values.student_profile.ra_number
                if values.student_profile
                else None,
                'disciplines': disciplines_list,
            }
        return values


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
            # Extrair disciplinas do relacionamento M:N
            disciplines_list = []
            if hasattr(values, 'teacher_profile') and values.teacher_profile:
                if hasattr(values.teacher_profile, 'disciplines'):
                    disciplines_list = [
                        {
                            'id': disc.id,
                            'name': disc.name,
                            'course_id': disc.course_id,
                            'prerequisites': (
                                [p.id for p in disc.prerequisites]
                                if disc.prerequisites
                                else []
                            ),
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
    role: str
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
    role: Optional[str] = None
