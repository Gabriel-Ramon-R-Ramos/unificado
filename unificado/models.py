from typing import Optional

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import Mapped, mapped_column, registry, relationship

table_registry = registry()

# Tabela de associação para relacionamento muitos-para-muitos entre
# disciplinas e pré-requisitos
discipline_prerequisites = Table(
    'discipline_prerequisites',
    table_registry.metadata,
    Column(
        'discipline_id',
        Integer,
        ForeignKey('disciplines.id'),
        primary_key=True,
    ),
    Column(
        'prerequisite_id',
        Integer,
        ForeignKey('disciplines.id'),
        primary_key=True,
    ),
)


@table_registry.mapped_as_dataclass
class Course:
    __tablename__ = 'courses'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(unique=True, index=True, nullable=False)

    disciplines: Mapped[list['Discipline']] = relationship(
        back_populates='course', init=False, default_factory=list
    )


@table_registry.mapped_as_dataclass
class Discipline:
    __tablename__ = 'disciplines'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    name: Mapped[str] = mapped_column(index=True, nullable=False)
    course_id: Mapped[int] = mapped_column(
        ForeignKey('courses.id'), nullable=False, index=True
    )

    course: Mapped['Course'] = relationship(
        back_populates='disciplines', init=False
    )

    prerequisites: Mapped[list['Discipline']] = relationship(
        secondary=discipline_prerequisites,
        primaryjoin=(
            'Discipline.id == discipline_prerequisites.c.discipline_id'
        ),
        secondaryjoin=(
            'Discipline.id == discipline_prerequisites.c.prerequisite_id'
        ),
        back_populates='dependent_disciplines',
        init=False,
        default_factory=list,
    )

    dependent_disciplines: Mapped[list['Discipline']] = relationship(
        secondary=discipline_prerequisites,
        primaryjoin=(
            'Discipline.id == discipline_prerequisites.c.prerequisite_id'
        ),
        secondaryjoin=(
            'Discipline.id == discipline_prerequisites.c.discipline_id'
        ),
        back_populates='prerequisites',
        init=False,
        default_factory=list,
    )


@table_registry.mapped_as_dataclass
class User:
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    username: Mapped[str] = mapped_column(
        String(100), unique=True, index=True, nullable=False
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, default='student'
    )  # 'student' | 'teacher' | 'admin'
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, init=False
    )

    # Perfis opcionais (one-to-one)
    student_profile: Mapped[Optional['StudentProfile']] = relationship(
        back_populates='user',
        init=False,
        uselist=False,
        cascade='all, delete-orphan',
    )
    teacher_profile: Mapped[Optional['TeacherProfile']] = relationship(
        back_populates='user',
        init=False,
        uselist=False,
        cascade='all, delete-orphan',
    )


@table_registry.mapped_as_dataclass
class StudentProfile:
    __tablename__ = 'student_profiles'

    # ID unico
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    # Relacionamento um-para-um com User
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False, unique=True, index=True
    )
    # Número de matrícula do aluno (opcional)
    ra_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relacionamento inverso com User
    user: Mapped['User'] = relationship(
        back_populates='student_profile',
        init=False,
        passive_deletes=True,
    )


@table_registry.mapped_as_dataclass
class TeacherProfile:
    __tablename__ = 'teacher_profiles'

    # ID unico
    id: Mapped[int] = mapped_column(primary_key=True, init=False)
    # Relacionamento um-para-um com User
    user_id: Mapped[int] = mapped_column(
        ForeignKey('users.id'), nullable=False, unique=True, index=True
    )
    # Número de matrícula do professor (opcional)
    employee_number: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True
    )

    # Relacionamento inverso com User
    user: Mapped['User'] = relationship(
        back_populates='teacher_profile',
        init=False,
        passive_deletes=True,
    )
